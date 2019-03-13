#include <iostream>
#include <chrono>

#include "cuda_runtime.h"
#include "device_launch_parameters.h"

#include "bbcu/bbcu.h"
#include "bbcu/bbcu_util.h"



//////////////////////////////
// common
//////////////////////////////

__device__ float device_fp32_LocalSum(float v, float *buf)
{
	buf[threadIdx.x] = v;
	__syncthreads();

	// スレッド間集計
	int comb = 1;
	while (comb < blockDim.x) {
		int next = comb * 2;
		int mask = next - 1;
		if ((threadIdx.x & mask) == 0) {
			buf[threadIdx.x] += buf[threadIdx.x + comb];
		}
		comb = next;
		__syncthreads();
	}

	return buf[0];
}



//////////////////////////////
// forward
//////////////////////////////

__global__ void kernal_fp32_BatchNormalization_Forward(
			const float*	x_buf,
			float*			y_buf,
			float*			gamma_buf,
			float*			beta_buf,
			float*			mean_buf,
			float*			rstd_buf,
			float*			running_mean_buf,
			float*			running_var_buf,
			float			momentum,
			float			reciprocal_frame_size,
			int				frame_size,
			int				frame_stride
		)
{
	extern __shared__   float	buf[];

	// 初期化
	int node = blockIdx.x;
	int frame = threadIdx.x;
	int frame_step = blockDim.x;
	
	// カハンの加算アルゴリズム(Kahan summation algorithm)
	float s1 = 0, c1 = 0, y1, t1;
	float s2 = 0, c2 = 0, y2, t2;
	const float* x_ptr = &x_buf[frame_stride * node];
	while (frame < frame_size) {
		float x = x_ptr[frame];

		y1 = x - c1;
		t1 = s1 + y1;
		c1 += (t1 - s1) - y1;
		s1 = t1;

		y2 = (x * x) - c2;
		t2 = s2 + y2;
		c2 += (t2 - s2) - y2;
		s2 = t2;

		frame += frame_step;
	}

	// 集計
	s1 = device_fp32_LocalSum(s1, buf);
	s2 = device_fp32_LocalSum(s2, buf);
	float mean = s1 * reciprocal_frame_size;
	float var = max(10e-7f, (s2 * reciprocal_frame_size) - (mean * mean));
	float rstd = rsqrt(var);

	if (threadIdx.x == 0) {
		running_mean_buf[node] = running_mean_buf[node] * momentum + mean * (1.0f - momentum);
		running_var_buf[node] = running_var_buf[node] * momentum + var * (1.0f - momentum);
		mean_buf[node] = mean;
		rstd_buf[node] = rstd;
	}

	// 正規化
	float gamma = gamma_buf[node];
	float beta  = beta_buf[node];
	float* y_ptr = &y_buf[frame_stride * node];
	frame = threadIdx.x;
	while (frame < frame_size) {
		float x = x_ptr[frame];
		x = (x - mean) * rstd;
		x = x * gamma + beta;
		y_ptr[frame] = x;
		frame += frame_step;
	}
}


CUBB_DLL_EXPORT int cubb_fp32_BatchNormalization_Forward
		(
			const float*	dev_x_buf,
			float*			dev_y_buf,
			float*			dev_gamma_buf,
			float*			dev_beta_buf,
			float*			dev_mean_buf,
			float*			dev_rstd_buf,
			float*			dev_running_mean_buf,
			float*			dev_running_var_buf,
			float			momentum,
			int				frame_size,
			int				frame_stride,
			int				node_size,	
			cudaStream_t    streamId
        )
{
	BBCU_DEBUG_ASSERT(bbcu_IsDeviceAvailable());

	int		unit_x = 512;

	dim3	grid(node_size);
	dim3	block(unit_x);

	kernal_fp32_BatchNormalization_Forward<<<grid, block, unit_x * sizeof(float), streamId>>> (
			dev_x_buf,
            dev_y_buf,
			dev_gamma_buf,
			dev_beta_buf,
			dev_mean_buf,
			dev_rstd_buf,
			dev_running_mean_buf,
			dev_running_var_buf,
			momentum,
			1.0f/ frame_size,
			frame_size,
			frame_stride
		);
	BB_CUDA_CHECK_LAST_ERROR();

	return 0;
}



//////////////////////////////
// backward
//////////////////////////////


__global__ void kernal_fp32_BatchNormalization_Backward
        (
			float const *x_buf,
			float const	*dy_buf,
			float		*dx_buf,
			float const *gamma_buf,
			float		*dgamma_buf,
			float		*dbeta_buf,
			float const *mean_buf,
			float const *rstd_buf,
			float		reciprocal_frame_size,
			int			frame_size,
			int			frame_stride
		)
{
	extern __shared__   float	buf[];

	// 初期化
	int node = blockIdx.x;
	int frame = threadIdx.x;
	int frame_step = blockDim.x;

	float mean = mean_buf[node];
	float rstd = rstd_buf[node];
	float gamma = gamma_buf[node];
	float dgamma = 0;
	float dbeta = 0;
	float dmeanx = 0;
	float dstd = 0;

	float rstd2 = rstd * rstd;

	float const *x_ptr  = &x_buf[node];
	float const *dy_ptr = &dy_buf[node];
	float		*dx_ptr = &dx_buf[node];

	while (frame < frame_size) {
		float x = x_ptr[frame];
		float dy = dy_ptr[frame];
		float xc = x - mean;
		float xn = xc * rstd;
		dbeta += dy;
		dgamma += xn * dy;

		float dxn = gamma * dy;
		dstd += dxn * xc * rstd2;
		dmeanx += dxn * rstd;

		frame += frame_step;
	}

	dbeta = device_fp32_LocalSum(dbeta, buf);
	dgamma = device_fp32_LocalSum(dgamma, buf);
	if (threadIdx.x == 0) {
		dgamma_buf[node] = dgamma;
		dbeta_buf[node] = dbeta;
	}
	dstd   = device_fp32_LocalSum(dstd, buf);
	dmeanx = device_fp32_LocalSum(dmeanx, buf);


	float dvar  = dstd * rstd;
	float dmean = (dmeanx - (mean * dvar)) * reciprocal_frame_size;

	frame = threadIdx.x;
	while (frame < frame_size) {
		float dy = dy_ptr[frame];
		float x  = x_ptr[frame];
		float dxn = dy * gamma;
		float dxc = dxn * rstd + dmean;
		float dx  = (x * dvar) * reciprocal_frame_size + dxc;
		dx_ptr[frame] = dx;
        frame += frame_step;
	}
}



CUBB_DLL_EXPORT int cubb_fp32_BatchNormalization_Backward
		(
			const float		*dev_x_buf,
			const float		*dev_dy_buf,
			float			*dev_dx_buf,
			float const		*dev_gamma_buf,
			float			*dev_dgamma_buf,
			float			*dev_dbeta_buf,
			float const		*dev_mean_buf,
			float const		*dev_rstd_buf,
			float			reciprocal_frame_size,
			int				frame_size,
			int				frame_stride,
			int				node_size,
            cudaStream_t    streamId
        )
{
	BBCU_DEBUG_ASSERT(bbcu_IsDeviceAvailable());

	int		unit_x = 512;

	dim3	grid(node_size);
	dim3	block(unit_x);

	kernal_fp32_BatchNormalization_Backward << <grid, block, unit_x * sizeof(float), streamId >> > (
            dev_x_buf,
            dev_dy_buf,
            dev_dx_buf,
            dev_gamma_buf,
            dev_dgamma_buf,
            dev_dbeta_buf,
            dev_mean_buf,
            dev_rstd_buf,
            reciprocal_frame_size,
            frame_size,
            frame_stride
        );
    BB_CUDA_CHECK_LAST_ERROR();
    
	return 0;
}

