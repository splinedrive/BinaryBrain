﻿// --------------------------------------------------------------------------
//  Binary Brain  -- binary neural net framework
//
//                                Copyright (C) 2018-2019 by Ryuji Fuchikami
//                                https://github.com/ryuz
//                                ryuji.fuchikami@nifty.com
// --------------------------------------------------------------------------



#pragma once


#include "bb/Manager.h"
#include "bb/Binarize.h"


namespace bb {


// ReLU(活性化層)
template <typename T = float>
class ReLU : public Binarize<T>
{
protected:
    bool        m_binary_mode = false;

    using Binarize<T>::m_host_only;
    using Binarize<T>::m_x_buf;
    FrameBuffer m_y_buf;

//    using Binarize<T>::m_y_buf;
//    using Binarize<T>::m_dx_buf;

protected:
    ReLU() {}

    /**
     * @brief  コマンド処理
     * @detail コマンド処理
     * @param  args   コマンド
     */
    void CommandProc(std::vector<std::string> args)
    {
        // バイナリモード設定
        if ( args.size() == 2 && args[0] == "binary" )
        {
            m_binary_mode = EvalBool(args[1]);
        }

        // HostOnlyモード設定
        if (args.size() == 2 && args[0] == "host_only")
        {
            m_host_only = EvalBool(args[1]);
        }
    }


public:
    static std::shared_ptr<ReLU> Create(void)
    {
        auto self = std::shared_ptr<ReLU>(new ReLU);
        return self;
    }

    ~ReLU() {}

    std::string GetClassName(void) const { return "ReLU"; }


    // 1ノードのみForward計算
    std::vector<double> ForwardNode(index_t node, std::vector<double> x_vec) const
    {
        if ( m_binary_mode ) {
            return Binarize<T>::ForwardNode(node, x_vec);
        }

        std::vector<double> y_vec;
        for ( auto x : x_vec ) {
            y_vec.push_back((x > 0.0) ? x : 0.0); // ReLU
        }

        return y_vec;
    }
    
    /**
     * @brief  forward演算
     * @detail forward演算を行う
     * @param  x     入力データ
     * @param  train 学習時にtrueを指定
     * @return forward演算結果
     */
    inline FrameBuffer Forward(FrameBuffer x_buf, bool train = true)
    {
        // binaryモード
        if (m_binary_mode) {
            return Binarize<T>::Forward(x_buf, train);
        }

        BB_ASSERT(x_buf.GetType() == DataType<T>::type);

        // 戻り値のサイズ設定
        FrameBuffer y_buf(x_buf.GetType(), x_buf.GetFrameSize(), x_buf.GetShape());

        // backward用に保存
        if ( train ) {
            m_x_buf = x_buf;
            m_y_buf = y_buf;
        }


#ifdef BB_WITH_CUDA
        if ( !m_host_only && x_buf.IsDeviceAvailable() && y_buf.IsDeviceAvailable() && Manager::IsDeviceAvailable() ) {
            // CUDA版
            auto ptr_x = x_buf.LockDeviceMemoryConst();
            auto ptr_y = y_buf.LockDeviceMemory(true);
            bbcu_fp32_ReLU_Forward(
                        (float const *)ptr_x.GetAddr(),
                        (float       *)ptr_y.GetAddr(),
                        (int          )x_buf.GetNodeSize(),
                        (int          )x_buf.GetFrameSize(),
                        (int          )(x_buf.GetFrameStride() / sizeof(float))
                    );
            return y_buf;
        }
#endif

        {
            // AVX版
            index_t frame_size = x_buf.GetFrameSize();
            index_t node_size  = x_buf.GetNodeSize();

            auto x_ptr = x_buf.template LockConst<float>();
            auto y_ptr = y_buf.template Lock<float>(true);

            index_t  m256_frame_size = (int)(((frame_size + 7) / 8) * 8);
            __m256 zero = _mm256_set1_ps(0);
            for (index_t node = 0; node < node_size; ++node) {
                auto x_addr = (float const *)x_ptr.GetAddr(node);
                auto y_addr = (float *)y_ptr.GetAddr(node);
                for (index_t frame = 0; frame < m256_frame_size; frame += 8) {
                    __m256 in_sig = _mm256_load_ps(&x_addr[frame]);
                    in_sig = _mm256_max_ps(in_sig, zero);
                    _mm256_store_ps(&y_addr[frame], in_sig);
                }
            }
            return y_buf;
        }

        {
            // 汎用版
            index_t frame_size = x_buf.GetFrameSize();
            index_t node_size  = x_buf.GetNodeSize();

            auto x_ptr = x_buf.template LockConst<T>();
            auto y_ptr = y_buf.template Lock<T>();

            // ReLU
    #pragma omp parallel for
            for (index_t node = 0; node < node_size; ++node) {
                for (index_t frame = 0; frame < frame_size; ++frame) {
                    auto sig = x_ptr.Get(frame, node);
                    y_ptr.Set(frame, node, sig > (T)0.0 ? sig : (T)0.0);
                }
            }
            return y_buf;
        }
    }


   /**
     * @brief  backward演算
     * @detail backward演算を行う
     *         
     * @return backward演算結果
     */
    inline FrameBuffer Backward(FrameBuffer dy_buf)
    {
        // binaryモード
        if (m_binary_mode) {
            return Binarize<T>::Backward(dy_buf);
        }

        BB_ASSERT(dy_buf.GetType() == DataType<T>::type);

        // 戻り値のサイズ設定
        FrameBuffer dx_buf(dy_buf.GetType(), dy_buf.GetFrameSize(), dy_buf.GetShape());

        FrameBuffer x_buf = m_x_buf;
        FrameBuffer y_buf = m_y_buf;
        m_x_buf = FrameBuffer();
        m_y_buf = FrameBuffer();

#ifdef BB_WITH_CUDA
        if ( DataType<T>::type == BB_TYPE_FP32 && !m_host_only
            && x_buf.IsDeviceAvailable() && dx_buf.IsDeviceAvailable() && dy_buf.IsDeviceAvailable() && Manager::IsDeviceAvailable() ) {
            // GPU版
            auto ptr_x  = x_buf.LockDeviceMemoryConst();
            auto ptr_dy = dy_buf.LockDeviceMemoryConst();
            auto ptr_dx = dx_buf.LockDeviceMemory(true);
            bbcu_fp32_ReLU_Backward(
                        (float const *)ptr_x.GetAddr(),
                        (float const *)ptr_dy.GetAddr(),
                        (float       *)ptr_dx.GetAddr(),
                        (int          )dy_buf.GetNodeSize(),
                        (int          )dy_buf.GetFrameSize(),
                        (int          )(dy_buf.GetFrameStride() / sizeof(float))
                    );
            return dx_buf;
        }
#endif

        if ( DataType<T>::type == BB_TYPE_FP32 ) {
            // AVX版
            index_t frame_size = dx_buf.GetFrameSize();
            index_t node_size = dx_buf.GetNodeSize();

            auto x_ptr  = x_buf.template LockConst<float>();
            auto y_ptr  = y_buf.template LockConst<float>();
            auto dy_ptr = dy_buf.template LockConst<float>();
            auto dx_ptr = dx_buf.template Lock<float>(true);

            index_t  m256_frame_size = (int)(((frame_size + 7) / 8) * 8);

            __m256 zero = _mm256_set1_ps(0);
            for (index_t node = 0; node < node_size; ++node) {
                auto y_addr  = (float *)y_ptr.GetAddr(node);
                auto dy_addr = (float *)dy_ptr.GetAddr(node);
                auto dx_addr = (float *)dx_ptr.GetAddr(node);
                for (index_t frame = 0; frame < m256_frame_size; frame += 8) {
                    __m256 y    = _mm256_load_ps(&y_addr[frame]);
                    __m256 dy   = _mm256_load_ps(&dy_addr[frame]);
                    __m256 mask = _mm256_cmp_ps(y, zero, _CMP_GT_OS);
                    __m256 dx   = _mm256_and_ps(dy, mask);
                    _mm256_store_ps(&dx_addr[frame], dx);
                }
            }
            return dx_buf;
        }

        {
            //汎用版
            index_t frame_size = dx_buf.GetFrameSize();
            index_t node_size = dx_buf.GetNodeSize();

            auto y_ptr  = y_buf.template LockConst<T>();
            auto dy_ptr = dy_buf.template LockConst<T>();
            auto dx_ptr = dx_buf.template Lock<T>();

            // ReLU
            #pragma omp parallel for
            for (index_t node = 0; node < node_size; ++node) {
                for (index_t frame = 0; frame < frame_size; ++frame) {
                    auto sig  = y_ptr.Get(frame, node);
                    auto grad = dy_ptr.Get(frame, node);
                    dx_ptr.Set(frame, node, (sig > (T)0) ? grad : (T)0);
                }
            }

            return dx_buf;
        }
    }
};


}

// end of file