﻿// --------------------------------------------------------------------------
//  Binary Brain  -- binary neural net framework
//
//                                 Copyright (C) 2018-2019 by Ryuji Fuchikami
//                                 https://github.com/ryuz
//                                 ryuji.fuchikami@nifty.com
// --------------------------------------------------------------------------


#pragma once

#include <set>

#include "bb/Model.h"
#include "bb/ShuffleSet.h"
#include "bb/Utility.h"


namespace bb {


// 入力接続数に制限のあるネット
template <typename FT = float, typename BT = float>
class SparseLayer : public Model
{
public:
    //ノードの 疎結合の管理
    virtual index_t GetNodeInputSize(index_t node) const = 0;
    virtual void    SetNodeInput(index_t node, index_t input_index, index_t input_node) = 0;
    virtual index_t GetNodeInput(index_t node, index_t input_index) const = 0;
    
    index_t GetNodeInputSize(indices_t node) const
    {
        return GetNodeInputSize(GetShapeIndex(node, this->GetOutputShape()));
    }
    void SetNodeInput(indices_t node, index_t input_index, indices_t input_node)
    {
        return SetNodeInput(GetShapeIndex(node, this->GetOutputShape()), input_index, GetShapeIndex(input_node, this->GetInputShape()));
    }
    void SetNodeInput(indices_t node, index_t input_index, index_t input_node)
    {
        return SetNodeInput(GetShapeIndex(node, this->GetOutputShape()), input_index, input_node);
    }
    indices_t GetNodeInput(indices_t node, index_t input_index) const
    {
        index_t input_node = GetOutputShape(GetShapeIndex(node, this->GetOutputShape()), input_index);
        return GetShapeIndices(input_node, this->GetInputShape());
    }

protected:
    void InitializeNodeInput(std::uint64_t seed, std::string connection = "")
    {
        auto input_shape  = this->GetInputShape();
        auto output_shape = this->GetOutputShape();

        auto input_node_size  = GetShapeSize(input_shape);
        auto output_node_size = GetShapeSize(output_shape);

        auto argv = SplitString(connection);

        if (argv.size() > 0 && argv[0] == "pointwise") {
            BB_ASSERT(input_shape.size() == 3);
            BB_ASSERT(output_shape.size() == 3);
            BB_ASSERT(input_shape[0] == output_shape[0]);
            BB_ASSERT(input_shape[1] == output_shape[1]);
            std::mt19937_64 mt(seed);
            for (index_t y = 0; y < output_shape[1]; ++y) {
                for (index_t x = 0; x < output_shape[0]; ++x) {
                    // 接続先をシャッフル
                    ShuffleSet<index_t> ss(input_shape[2], mt());
                    for (index_t c = 0; c < output_shape[2]; ++c) {
                        // 入力をランダム接続
                        index_t  input_size = GetNodeInputSize({x, y, c});
                        auto random_set = ss.GetRandomSet(input_size);
                        for (index_t i = 0; i < input_size; ++i) {
                            SetNodeInput({x, y, c}, i, {x, y, random_set[i]});
                        }
                    }
                }
            }
            return;
        }

        if (argv.size() > 0 && argv[0] == "depthwise") {
            BB_ASSERT(input_shape.size() == 3);
            BB_ASSERT(output_shape.size() == 3);
            BB_ASSERT(input_shape[2] == output_shape[2]);
            std::mt19937_64 mt(seed);
            for (index_t c = 0; c < output_shape[2]; ++c) {
                // 接続先をシャッフル
                ShuffleSet<index_t> ss(input_shape[0] * input_shape[1], mt());
                for (index_t y = 0; y < output_shape[1]; ++y) {
                    for (index_t x = 0; x < output_shape[0]; ++x) {
                        // 入力をランダム接続
                        index_t  input_size = GetNodeInputSize({x, y, c});
                        auto random_set = ss.GetRandomSet(input_size);
                        for (index_t i = 0; i < input_size; ++i) {
                            index_t iy = random_set[i] / input_shape[0];
                            index_t ix = random_set[i] % input_shape[0];

                            index_t output_node = GetShapeIndex({x, y, c}, output_shape);
                            index_t input_node  = GetShapeIndex({ix, iy, c}, input_shape);

                            BB_ASSERT(output_node >= 0 && output_node < output_node_size);
                            BB_ASSERT(input_node  >= 0 && input_node  < input_node_size);
                            SetNodeInput(output_node, i, input_node);
                        }
                    }
                }
            }
            return;
        }

        if ( argv.size() > 0 && argv[0] == "gauss" ) {
            // ガウス分布で結線
            int n = (int)input_shape.size();
            std::vector<double> step(n);
            std::vector<double> sigma(n);
            for (int i = 0; i < n; ++i) {
                step[i]  = (double)(input_shape[i] - 1) / (double)(output_shape[i] - 1);
                sigma[i] = (double)input_shape[i] / (double)output_shape[i];
            }

            std::mt19937_64                     mt(seed);
            std::normal_distribution<double>    norm_dist(0.0, 1.0);
            indices_t           output_index(n, 0);
            do {
                // 入力の参照基準位置算出
                std::vector<double> input_offset(n);
                for (int i = 0; i < n; ++i) {
                    input_offset[i] = output_index[i] * step[i];
                }

                auto output_node = GetShapeIndex(output_index, output_shape);
                auto m = GetNodeInputSize(output_node);
                std::set<index_t>   s;
                std::vector<double> input_position(n);
                for ( int i = 0; i < m; ++i ) {
                    for ( ; ; ) {
                        for ( int j = 0; j < n; ++j ) {
                            input_position[j] = input_offset[j] + norm_dist(mt) * sigma[j];
                        }
                        auto input_index = RegurerlizeIndices(input_position, input_shape);
                        auto input_node  = GetShapeIndex(input_index, input_shape);
                        if ( s.count(input_node) == 0 ){
                            SetNodeInput(output_node, i, input_node);
                            s.insert(input_node);
                            break;
                        }
                    }
                }
            } while ( GetNextIndices(output_index, output_shape) );
            return;
        }

#if 0
        if ( input_shape.size() == 3 && input_shape[2] > 3) {
            index_t c = input_shape[2];
            index_t h = input_shape[1];
            index_t w = input_shape[0];
            indices_t offset_shape({w, h, 3});

            ShuffleSet<index_t> ss(3*h*w, seed);
            indices_t idx({0, 0, 0});
            for (index_t node = 0; node < output_node_size; ++node) {
                index_t  input_size = GetNodeInputSize(node);

                auto random_set = ss.GetRandomSet(input_size);
                for (index_t i = 0; i < input_size; ++i) {
                    indices_t offset_idx = GetShapeIndices(random_set[i], offset_shape);
                    indices_t input_idx(3);
                    input_idx[2] = (idx[2] + offset_idx[2]) % c;
                    input_idx[1] = (idx[1] + offset_idx[1]) % h;
                    input_idx[0] = (idx[0] + offset_idx[0]) % w;
                    SetNodeInput(node, i, GetShapeIndex(input_idx, input_shape));
                }

                GetNextIndices(idx, input_shape);
            }
            return;
        }
#endif
        if ( argv.size() > 0 && argv[0] == "serial" ) {
            // 連番結線
            index_t input_node = 0;
            for ( index_t output_node = 0; output_node < output_node_size; ++output_node ) {
                index_t m = GetNodeInputSize(output_node);
                for ( index_t i = 0; i < m; ++i ) {
                    SetNodeInput(output_node, i, input_node % input_node_size);
                    ++input_node;
                }
            }
            return;
        }

        if ( argv.size() == 0 || argv[0] == "random" ) {
            // ランダム結線
            ShuffleSet<index_t> ss(input_node_size, seed);    // 接続先をシャッフル
            for (index_t node = 0; node < output_node_size; ++node) {
                // 入力をランダム接続
                index_t  input_size = GetNodeInputSize(node);
                auto random_set = ss.GetRandomSet(input_size);
                for (index_t i = 0; i < input_size; ++i) {
                    SetNodeInput(node, i, random_set[i]);
                }
            }
            return;
        }

        std::cout << "unknown connection rule : \"" << argv[0] <<  "\"" << std::endl;
        BB_ASSERT(0);
    }
};


}

