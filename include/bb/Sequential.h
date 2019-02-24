﻿// --------------------------------------------------------------------------
//  Binary Brain  -- binary neural net framework
//
//                                     Copyright (C) 2018 by Ryuji Fuchikami
//                                     https://github.com/ryuz
//                                     ryuji.fuchikami@nifty.com
// --------------------------------------------------------------------------


#pragma once

#include <vector>


#include "bb/Layer.h"


namespace bb {


//! layer class
class Sequential : public Layer
{
protected:
	std::vector< std::shared_ptr<Layer> > m_layers;

public:
    Sequential() {}

    /**
     * @brief  デストラクタ(仮想関数)
     * @detail デストラクタ(仮想関数)
     */
	~Sequential() {}

    /**
     * @brief  クラス名取得
     * @detail クラス名取得
     *         シリアライズ時などの便宜上、クラス名を返すようにする
     * @return クラス名
     */
    std::string GetClassName(void) const
    {
        return "Sequential";
    }

    void Add(std::shared_ptr<Layer> layer)
    {
        m_layers.push_back(layer);
    }
	
	
//	virtual void  Command(std::string command) {}								// コマンドを送信
	
    // バイナリモードを設定
    void  SetBinaryMode(bool enable)
    {
        for (auto layer : m_layers) {
            layer->SetBinaryMode(enable);
        }
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
        for (auto layer : m_layers) {
            parameters.PushBack(layer->GetParameters());
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
        for (auto layer : m_layers) {
            gradients.PushBack(layer->GetGradients());
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
        for (auto layer : m_layers) {
            shape = layer->SetInputShape(shape);
        }
        return shape;
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
        for (auto layer : m_layers) {
            x = layer->Forward(x, train);
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
        for (auto it = m_layers.rbegin(); it != m_layers.rend(); ++it) {
            dy = (*it)->Backward(dy);
        }
        return dy; 
    }
	

public:


	void Save(cereal::JSONOutputArchive& archive) const
	{
        for (auto layer : m_layers) {
            layer->Save(archive);
        }
	}

	void Load(cereal::JSONInputArchive& archive)
	{
        for (auto layer : m_layers) {
            layer->Load(archive);
        }
	}
};



}