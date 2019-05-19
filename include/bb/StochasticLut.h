﻿// --------------------------------------------------------------------------
//  Binary Brain  -- binary neural net framework
//
//                                     Copyright (C) 2018 by Ryuji Fuchikami
//                                     https://github.com/ryuz
//                                     ryuji.fuchikami@nifty.com
// --------------------------------------------------------------------------



#pragma once

#include <cstdint>
#include <random>

#include "bb/Model.h"
#include "bb/StochasticLut2.h"
#include "bb/StochasticLut4.h"
#include "bb/StochasticLut6.h"
#include "bb/BatchNormalization.h"


namespace bb {


// Sparce Mini-MLP(Multilayer perceptron) Layer [Affine-ReLU-Affine-BatchNorm-Binarize]
template <int N = 6, typename T = float >
class StochasticLut : public SparseLayer
{
    using _super = SparseLayer;

protected:
    // 2層で構成
    std::shared_ptr< SparseLayer >              m_lut;
    std::shared_ptr< BatchNormalization<T> >    m_batch_norm;

    bool                                        m_bn_enable = true;

protected:
    StochasticLut() {}

    /**
     * @brief  コマンド処理
     * @detail コマンド処理
     * @param  args   コマンド
     */
    void CommandProc(std::vector<std::string> args)
    {
        // BatchNormalization設定
        if ( args.size() == 2 && args[0] == "batch_normalization" )
        {
            m_bn_enable = EvalBool(args[1]);
        }
    }

public:
    ~StochasticLut() {}

    struct create_t
    {
        indices_t  output_shape;
        bool       bn_enable = true;
        T          momentum = (T)0.001;
        T          gamma    = (T)0.2;
        T          beta     = (T)0.5;
        bool       fix_gamma = true;
        bool       fix_beta = true;
    };

    static std::shared_ptr< StochasticLut > Create(create_t const &create)
    {
        auto self = std::shared_ptr<StochasticLut>(new StochasticLut);
        switch ( N ) {
        case 2: self->m_lut = StochasticLut2<T>::Create(create.output_shape);   break;
        case 4: self->m_lut = StochasticLut4<T>::Create(create.output_shape);   break;
        case 6: self->m_lut = StochasticLut6<T>::Create(create.output_shape);   break;
        default: BB_ASSERT(0);  break;
        }

        typename BatchNormalization<T>::create_t bn_create;
        bn_create.momentum  = create.momentum;
        bn_create.gamma     = create.gamma; 
        bn_create.beta      = create.beta;    
        bn_create.fix_gamma = create.fix_gamma;
        bn_create.fix_beta  = create.fix_beta;
        self->m_batch_norm = BatchNormalization<T>::Create(bn_create);
        return self;
    }

    static std::shared_ptr< StochasticLut > Create(indices_t output_shape, bool bn_enable = true, T momentum = (T)0.001, T gamma = (T)0.5, T beta = (T)0.5)
    {
        create_t create;
        create.output_shape = output_shape;
        create.bn_enable    = bn_enable;
        create.momentum     = momentum;
        create.gamma        = gamma;
        create.beta         = beta;
        return Create(create);
    }

    static std::shared_ptr< StochasticLut > Create(index_t output_node_size, bool bn_enable = true, T momentum = (T)0.001, T gamma = (T)0.5, T beta = (T)0.5)
    {
        create_t create;
        create.output_shape = indices_t({output_node_size});
        create.bn_enable    = bn_enable;
        create.momentum     = momentum;
        create.gamma        = gamma;
        create.beta         = beta;
        return Create(create);
    }

    std::string GetClassName(void) const { return "StochasticLut"; }

    /**
     * @brief  コマンドを送る
     * @detail コマンドを送る
     */   
    void SendCommand(std::string command, std::string send_to = "all")
    {
        _super::SendCommand(command, send_to);

        m_lut       ->SendCommand(command, send_to);
        m_batch_norm->SendCommand(command, send_to);
    }
    
    /**
     * @brief  パラメータ取得
     * @detail パラメータを取得する
     *         Optimizerでの利用を想定
     * @return パラメータを返す
     */
    Variables GetParameters(void)
    {
        Variables parameters;
        parameters.PushBack(m_lut->GetParameters());
        if ( m_bn_enable ) {
            parameters.PushBack(m_batch_norm->GetParameters());
        }
        return parameters;
    }

    /**
     * @brief  勾配取得
     * @detail 勾配を取得する
     *         Optimizerでの利用を想定
     * @return パラメータを返す
     */
    virtual Variables GetGradients(void)
    {
        Variables gradients;
        gradients.PushBack(m_lut       ->GetGradients());
        if ( m_bn_enable ) {
            gradients.PushBack(m_batch_norm->GetGradients());
        }
        return gradients;
    }  

    /**
     * @brief  入力形状設定
     * @detail 入力形状を設定する
     *         内部変数を初期化し、以降、GetOutputShape()で値取得可能となることとする
     *         同一形状を指定しても内部変数は初期化されるものとする
     * @param  shape      1フレームのノードを構成するshape
     * @return 出力形状を返す
     */
    indices_t SetInputShape(indices_t shape)
    {
        shape = m_lut->SetInputShape(shape);
        shape = m_batch_norm->SetInputShape(shape);
        return shape;
    }

    /**
     * @brief  入力形状取得
     * @detail 入力形状を取得する
     * @return 入力形状を返す
     */
    indices_t GetInputShape(void) const
    {
        return m_lut->GetInputShape();
    }

    /**
     * @brief  出力形状取得
     * @detail 出力形状を取得する
     * @return 出力形状を返す
     */
    indices_t GetOutputShape(void) const
    {
        return m_lut->GetOutputShape();
    }
    
    index_t GetNodeInputSize(index_t node) const
    {
        return m_lut->GetNodeInputSize(node);
    }

    void SetNodeInput(index_t node, index_t input_index, index_t input_node)
    {
        m_lut->SetNodeInput(node, input_index, input_node);
    }

    index_t GetNodeInput(index_t node, index_t input_index) const
    {
        return m_lut->GetNodeInput(node, input_index);
    }

    std::vector<double> ForwardNode(index_t node, std::vector<double> x_vec) const
    {
        index_t input_size = this->GetNodeInputSize(node);
        BB_ASSERT(input_size == x_vec.size());

        x_vec = m_lut->ForwardNode(node, x_vec);

        if ( m_bn_enable ) {
            x_vec = m_batch_norm->ForwardNode(node, x_vec);
        }

        return x_vec;
    }

   /**
     * @brief  forward演算
     * @detail forward演算を行う
     * @param  x     入力データ
     * @param  train 学習時にtrueを指定
     * @return forward演算結果
     */
    FrameBuffer Forward(FrameBuffer x, bool train = true)
    {
        x = m_lut->Forward(x, train);
        if ( m_bn_enable ) {
            x = m_batch_norm->Forward(x, train);
        }
        return x;
    }

   /**
     * @brief  backward演算
     * @detail backward演算を行う
     *         
     * @return backward演算結果
     */
    FrameBuffer Backward(FrameBuffer dy)
    {
        if ( m_bn_enable ) {
            dy = m_batch_norm->Backward(dy);
        }
        dy = m_lut->Backward(dy);
        return dy; 
    }

protected:
    /**
     * @brief  モデルの情報を表示
     * @detail モデルの情報を表示する
     * @param  os     出力ストリーム
     * @param  indent インデント文字列
     */
    void PrintInfoText(std::ostream& os, std::string indent, int columns, int nest, int depth)
    {
        // これ以上ネストしないなら自クラス概要
        if ( depth > 0 && (nest+1) >= depth ) {
            Model::PrintInfoText(os, indent, columns, nest, depth);
        }
        else {
            // 子レイヤーの表示
            m_lut->PrintInfo(depth, os, columns, nest+1);
            if ( m_bn_enable ) {
                m_batch_norm->PrintInfo(depth, os, columns, nest+1);
            }
        }
    }

public:
    // Serialize
    void Save(std::ostream &os) const 
    {
        m_lut->Save(os);
        m_batch_norm->Save(os);
    }

    void Load(std::istream &is)
    {
        m_lut->Load(is);
        m_batch_norm->Load(is);
    }


#ifdef BB_WITH_CEREAL
    template <class Archive>
    void save(Archive& archive, std::uint32_t const version) const
    {
        _super::save(archive, version);
    }

    template <class Archive>
    void load(Archive& archive, std::uint32_t const version)
    {
        _super::load(archive, version);
    }

    void Save(cereal::JSONOutputArchive& archive) const
    {
        archive(cereal::make_nvp("StochasticLut", *this));
        m_lut       ->Save(archive);
        m_batch_norm->Save(archive);
    }

    void Load(cereal::JSONInputArchive& archive)
    {
        archive(cereal::make_nvp("StochasticLut", *this));
        m_lut       ->Load(archive);
        m_batch_norm->Load(archive);
    }
#endif

};


}