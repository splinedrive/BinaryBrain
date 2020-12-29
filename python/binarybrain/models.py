# -*- coding: utf-8 -*-

import pickle
import numpy as np
from typing import List

import binarybrain      as bb
import binarybrain.core as core


# ------- 基本モデル --------

class Model():
    """Model class
       ネットワーク各層の演算モデルの基底クラス
       すべてのモデルはこのクラスを基本クラスに持つ

       BinaryBrain では、モデルを実際にインスタンスとして生成して組み合わせることで
       学習ネットワークを構成する。特にネットワーク内のインスタンス化された
       モデルをレイヤーという呼び方をする場合がある。
    """
    
    def __init__(self, *, core_model=None, input_shape=None, name=None):
        if core_model is not None:
            self.core_model = core_model
            if name is not None:
                self.core_model.set_name(name)
            if input_shape is not None:
                self.set_input_shape(input_shape)
    
    def get_core(self):
        return self.core_model
    
    def set_name(self, name: str):
        """インスタンス名の設定

           生成したモデルには任意の名前を付けることが可能であり、表示や
           保存時のファイル名などに利用することが可能である

        Args:
            name (str): 新しいインスタンス名
        """
        return self.get_core().set_name(name)

    def get_name(self):
        """インスタンス名の取得

           インスタンス名を取得する。名称が設定されていない場合はクラス名が返される

        Returns:
            name (str)
        """
        return self.get_core().get_name()

    def is_named(self):
        """インスタンス名の設定確認

           インスタンス名が設定されているかどうか確認する

        Returns:
            named (bool)
        """
        return self.get_core().is_named()
    
    def get_class_name(self):
        """クラス名の取得

           クラス名(=モデル名)を取得する。

        Returns:
            class name (str)
        """
        return self.get_core().get_class_name()
    
    def get_info(self, depth=0, *, columns=70, nest=0):
        """モデル情報取得

           モデルの情報表示用の文字列を取得する
           そのまま表示やログに利用することを想定している

        Returns:
            info (str)
        """
        return self.get_core().get_info(depth, columns, nest)
    
    def send_command(self, command, send_to='all'):
        """コマンドの送信

           モデルごとにコマンド文字列で設定を行う
           コマンド文字列の定義はモデルごとに自由である
           Sequentialクラスなどは、保有する下位のモデルに再帰的にコマンドを
           伝搬させるので、複数の層に一括した設定が可能である
           受取先は send_to で送り先はインスタンス名やクラス名で制限でき 'all' を指定すると
           フィルタリングされない

        Args:
            command (str): コマンド文字列
            send_to (str): 送信先
        """
        self.get_core().send_command(command, send_to)
    
    def set_input_shape(self, input_shape: [int]):
        """入力シェイプ設定

           BinaryBarainではモデル生成時に入力のシェイプを決定する必要はなく
           ネットワーク構築後に、ネットワークを構成する各モデルの
           set_input_shape を順に呼び出して形状を伝搬させることで
           各モデルの形状の設定を簡易化できる

           set_input_shape が呼ばれるとそれまでの各層で保有する情報は
           保証されない。ネットワーク構築後に一度だけ呼び出すことを想定している
        
        Args:
            input_shape (List[int]): 入力シェイプ

        Returns:
            output_shape (List[int]): 出力シェイプ
        """
        return self.get_core().set_input_shape(input_shape)

    def get_input_shape(self) -> [int]:
        """入力シェイプ取得

        Returns:
            input_shape (List[int]): 入力シェイプ
        """
        return self.get_core().get_input_shape()

    def get_output_shape(self) -> [int]:
        """出力シェイプ取得

        Returns:
            output_shape (List[int]): 出力シェイプ
        """
        return self.get_core().get_output_shape()

    def get_input_node_size(self) -> int:
        return self.get_core().get_input_node_size()

    def get_output_node_size(self) -> int:
        return self.get_core().get_output_node_size()

    def get_parameters(self):
        """パラメータ変数取得

           学習対象とするパラメータ群を Variables として返す
           主に最適化(Optimizer)に渡すことを目的としている

           モデル側を自作する際には、このメソッドで戻す変数の中に
           含めなかったパラメータは学習対象から外すことができる為
           パラメータを凍結したい場合などに利用できる

        Returns:
            parameters (Variables): パラメータ変数
        """
        return bb.Variables.from_core(self.get_core().get_parameters())
    
    def get_gradients(self):
        """勾配変数取得

           get_parameters と対になる勾配変数を Variables として返す
           主に最適化(Optimizer)に渡すことを目的としている

        Returns:
            gradients (Variables): 勾配変数
        """
        return bb.Variables.from_core(self.get_core().get_gradients())
    
    def forward(self, x_buf, train=True):
        """Forward

           モデルは学習および推論の為に forward メソッドを持つ
            train 変数を
        
        Args:
            x_buf (FrameBuffer): 入力データ
            train (bool) : Trueで学習、Falseで推論

        Returns:
            y_buf (FrameBuffer): 出力データ
        """
        return bb.FrameBuffer.from_core(self.get_core().forward(x_buf.get_core(), train))
    
    def backward(self, dy_buf):
        """Backward

           モデルは学習の為に backword メソッドを持つ
           必ず forwad と対で呼び出す必要があり、直前の forward 結果に対する
           勾配計算を行いながら逆伝搬する

           BinaryBrain は自動微分の機能を備えないので、backword の実装は必須である
        
        Args:
            dy_buf (FrameBuffer): 入力データ

        Returns:
            dx_buf (FrameBuffer): 出力データ
        """
        return bb.FrameBuffer.from_core(self.get_core().backward(dy_buf.get_core()))
    
    def dump_bytes(self):
        """バイトデータにシリアライズ

           モデルのデータをシリアライズして保存するためのバイト配列を生成
        
        Returns:
            data (bytes): Serialize data
        """
        return self.get_core().dump()
    
    def load_bytes(self, data):
        """バイトデータをロード

           モデルのデータをシリアライズして復帰のバイト配列ロード
        
        Args:
            data (bytes): Serialize data
        """
        self.get_core().load(data)
    
    def dump(self, f):
        pickle.dump(f, self.dump_bytes())
    
    def load(self, f):
        self.load_bytes(pickle.load(f))
    
    
    
        
class Sequential(Model):
    """Sequential class
       複数レイヤーを直列に接続してグルーピングするクラス

       リストの順番で set_input_shape, forward, backward などを実行する
       また send_command の子レイヤーへのブロードキャストや、
       get_parameters, get_gradients の統合を行うことで複数のレイヤーを
       １つのレイヤーとして操作できる

    Args:
        model_list (List[Model]): モデルのリスト
    """
    
    def __init__(self, model_list=[], *, name=None):
        super(Sequential, self).__init__()
        self.model_list  = model_list
        self.name        = name

    def get_core(self):
        # C++のコアの同機能に渡してしまうと Python からの扱いが不便になるので普段はListで管理して必要な時のみ変換する       
        core_model = core.Sequential.create()
        for model in self.model_list:
            core_model.add(model.get_core())
        if self.name is not None:
            core_model.set_name(self.name)            
        return core_model
    
    def set_model_list(self, model_list):
        """モデルリストの設定
       
        Args:
            model_list (List[Model]): モデルのリスト
        """
        self.model_list = model_list
    
    def get_model_list(self):
        """モデルリストの取得
       
        Returns:
            model_list (List[Model]): モデルのリスト
        """
        return self.model_list
    
    def __len__(self):
        return len(self.model_list)
    
    def __iter__(self):
        return self.model_list.__iter__()
    
    def __getitem__(self, item):
        return self.model_list[item]
    
    def __setitem__(self, item, model):
        self.model_list[item] = model
    
    def append(self, model):
        """モデルリストの追加
       
        Returns:
            model (Model): リストに追加するモデル
        """
        self.model_list.append(model)
    
    def send_command(self, command, send_to="all"):
        for model in self.model_list:
            model.send_command(command=command, send_to=send_to)
    
    def set_input_shape(self, shape):
        self.input_shape = shape
        for model in self.model_list:
            shape = model.set_input_shape(shape)
        return shape

    def get_parameters(self):
        variables = bb.Variables()
        for model in self.model_list:
            variables.append(model.get_parameters())
        return variables

    def get_gradients(self):
        variables = bb.Variables()
        for model in self.model_list:
            variables.append(model.get_gradients())
        return variables
    
    def forward(self, x_buf, train=True):
        for model in self.model_list:
            x_buf = model.forward(x_buf, train)
        return x_buf

    def backward(self, dy_buf):
        for model in reversed(self.model_list):
            dy_buf = model.backward(dy_buf)
        return dy_buf


# ------- バイナリ変調 --------

class RealToBinary(Model):
    """RealToBinary class
        実数値をバイナリ値に変換する。
        バイナリ変調機能も有しており、フレーム方向に変調した場合フレーム数(=ミニバッチサイズ)が
        増える。
        またここでビットパッキングが可能であり、32フレームのbitをint32に詰め込みメモリ節約可能である

    Args:
        frame_modulation_size (int): フレーム方向への変調数(フレーム数が増える)
        depth_modulation_size (int): Depth方向への変調数(チャンネル数が増える)
        framewise (bool): Trueで変調閾値をフレーム単位とする(Falseでピクセル単位)
        bin_dtype (DType): 出力の型を bb.DType.FP32 もしくは bb.DType.BIT で指定可能
    """
    
    def __init__(self, *,
                     input_shape=None, frame_modulation_size=1, depth_modulation_size=1, value_generator=None,
                     framewise=False, input_range_lo=0.0, input_range_hi=1.0, name=None, bin_dtype=bb.DType.FP32):
        try:
            core_creator = {
                bb.DType.FP32: core.RealToBinary_fp32.create,
                bb.DType.BIT:  core.RealToBinary_bit.create,
            }[bin_dtype]
        except KeyError:
            raise TypeError("unsupported")

        core_model = core_creator(frame_modulation_size, depth_modulation_size,
                            value_generator, framewise, input_range_lo, input_range_hi)
        super(RealToBinary, self).__init__(core_model=core_model, input_shape=input_shape, name=name)

        
class BinaryToReal(Model):
    """BinaryToReal class
        バイナリ値を実数値に戻す。その際にフレーム方向に変調されたデータを積算して
        元に戻すことが可能である

    Args:
        frame_modulation_size (int): フレーム方向への変調数(フレーム分積算)
        output_shape (List[int]): 出力のシェイプ(必要に応じて積算)
        bin_dtype (DType): 入力の型を bb.DType.FP32 もしくは bb.DType.BIT で指定可能
    """
    
    def __init__(self, *, frame_modulation_size=1, output_shape=[], input_shape=None, name=None, bin_dtype=bb.DType.FP32):
        try:
            core_creator = {
                bb.DType.FP32: core.BinaryToReal_fp32.create,
                bb.DType.BIT:  core.BinaryToReal_bit.create,
            }[bin_dtype]
        except KeyError:
            raise TypeError("unsupported")
        
        core_model = core_creator(frame_modulation_size=frame_modulation_size, output_shape=output_shape)
        
        super(BinaryToReal, self).__init__(core_model=core_model, input_shape=input_shape, name=name)


class BitEncode(Model):
    """BitEncode class
        実数値をバイナリ表現としてdepth方向に展開する

    Args:
        bit_size (int): エンコードするbit数
    """

    def __init__(self, bit_size=1, *, output_shape=[], input_shape=None, name=None, bit_dtype=bb.DType.FP32, real_dtype=bb.DType.FP32):

        try:
            core_creator = {
                bb.DType.FP32: core.BitEncode_fp32.create,
                bb.DType.BIT:  core.BitEncode_bit.create,
            }[bit_dtype]
        except KeyError:
            raise TypeError("unsupported")
        
        core_model = core_creator(bit_size, output_shape)

        super(BitEncode, self).__init__(core_model=core_model, input_shape=input_shape, name=name)


class Reduce(Model):
    """Reduce class
        多重化されている出力を折り返して積和する

    Args:
        output_shape ([int]): 出力のシェイプ
    """

    def __init__(self, output_shape, *, input_shape=None, name=None, fw_dtype=bb.DType.FP32, bw_dtype=bb.DType.FP32):

        try:
            core_creator = {
                bb.DType.FP32: core.Reduce_fp32.create,
                bb.DType.BIT:  core.Reduce_bit.create,
            }[fw_dtype]
        except KeyError:
            raise TypeError("unsupported")
        
        core_model = core_creator(output_shape)

        super(Reduce, self).__init__(core_model=core_model, input_shape=input_shape, name=name)


# ------- 演算 --------

class DenseAffine(Model):
    """DenseAffine class
       普通のDenseAffine

    Args:
        output_shape (List[int]): 出力のシェイプ
        initialize_std (float) : 重み初期化乱数の標準偏差
        initializer (str): 変数の初期化アルゴリズム選択。今のところ 'he' のみ
        seed (int): 変数初期値などの乱数シード
    """
    
    def __init__(self, output_shape, *, input_shape=None, initialize_std=0.01, initializer='he', seed=1, name=None):
        core_creator = core.DenseAffine.create
        
        core_model = core_creator(output_shape=output_shape, initialize_std=initialize_std, initializer=initializer, seed=seed)
        
        super(DenseAffine, self).__init__(core_model=core_model, input_shape=input_shape, name=name)


class DepthwiseDenseAffine(Model):
    """DepthwiseDenseAffine class

       Convolution2d と組み合わせて、普通の Depthwise Convolution を作るためのクラス

    Args:
        output_shape (List[int]): 出力のシェイプ
        input_point_size (int): 入力のpoint数
        depth_size (int): depthサイズ
        initialize_std (float) : 重み初期化乱数の標準偏差
        initializer (str): 変数の初期化アルゴリズム選択。今のところ 'he' のみ
        seed (int): 変数初期値などの乱数シード
    """
    
    def __init__(self, output_shape, *, input_shape=None, input_point_size=0, depth_size=0, initialize_std=0.01, initializer='he', seed=1, name=None):
        core_creator = core.DepthwiseDenseAffine.create
        
        core_model = core_creator(output_shape=output_shape, initialize_std=initialize_std, initializer=initializer, seed=seed)
        
        super(DepthwiseDenseAffine, self).__init__(core_model=core_model, input_shape=input_shape, name=name)


class SparseModel(Model):
    """疎結合の基底モデル
    """

    def get_node_connection_size(self, output_node):
        return self.get_core().get_node_connection_size(output_node)

    def set_node_connection_index(self, output_node, connection, input_node):
        self.get_core().set_node_connection_index(output_node, connection, input_node)

    def get_node_connection_index(self, output_node, connection):
        return self.get_core().get_node_connection_index(output_node, connection)

    def get_lut_table_size(self, node):
        return self.get_core().get_lut_table_size(node)

    def get_lut_table(self, node, bitpos):
        return self.get_core().get_lut_table(node, bitpos)


    def get_connection_list(self):
        """接続リスト取得
            
            各出力ノードの入力に対する接続を二次元リストで返す
            入出力のシェイプにかかわらず両者が flatten された状態で処理される

        Returns:
            connection_list (List[List[int]]) : 接続リスト
        """

        connection_list = []
        rows = self.get_output_node_size()
        for i in range(rows):
            node_list = []
            cols = self.get_node_connection_size(i)
            for j in range(cols):
                node_list.append(self.get_node_connection_index(i, j))
            connection_list.append(node_list)
        return connection_list

    def set_connection_list(self, connection_list):
        """接続行列設定
            
            各出力ノードの入力に対する接続を二次元リストで設定する
            入出力のシェイプにかかわらず両者が flatten された状態で2次元リストとする

        Args:
            connection_list (List[List[int]]) : 接続リスト
        """

        input_node_size = self.get_input_node_size()
        rows = self.get_output_node_size()
        assert(len(connection_list) == rows)
        for i in range(rows):
            cols = self.get_node_connection_size(i)
            assert(len(connection_list[i]) == cols)
            for j in range(cols):
                index = int(connection_list[i][j])
                assert(index>= 0 and index < input_node_size)
                self.set_node_connection_index(i, j, index)

    def get_lut_table_list(self):
        """LUTテーブルのリスト取得

        Returns:
            lut_list (List[List[int]]) : 接続行列
        """

        lut_list = []
        rows = self.get_output_node_size()
        for i in range(rows):
            bit_list = []
            cols = self.get_lut_table_size(i)
            for j in range(cols):
                bit_list.append(self.get_lut_table(i, j))
            lut_list.append(bit_list)
        return lut_list


class DifferentiableLut(SparseModel):
    """DifferentiableLut class
        微分可能LUTモデル

        内部計算的には StocasticLUT + BatchNormalization + Binarize(HardTanh) で構成される

        FPGA合成するためのルックアップテーブル型のモデルを学習することができる
        純粋な Stochastic 演算のみを行いたい場合は binarize と batch_norm の両方を False にすればよい。
        
    Args:
        output_shape (List[int]): 出力のシェイプ
        connection(str): 結線ルールを 'random', 'serial', 'depthwise' から指定可能
        batch_norm (bool): BatchNormalization を有効にするか
        momentum (float): BatchNormalization を有効にするか
        gamma (float): BatchNormalization を有効にするか
        beta (float): BatchNormalization を有効にするか
        N (int): LUTの入力数
        seed (int): 変数初期値などの乱数シード
        bin_dtype (DType)): バイナリ出力の型を bb.DType.FP32 と bb.DType.BIT から指定(bb.DType.BIT は binarize=True 時のみ)
    """
    
    def __init__(self, output_shape, *, input_shape=None,
                    connection='random', binarize=True, batch_norm=True, momentum=0.0, gamma= 0.3, beta=0.5, seed=1,
                    name=None, N=6, bin_dtype=bb.DType.FP32, real_dtype=bb.DType.FP32):
        
        # 設定に応じて機能をパッキングしたモデルが使える場合は自動選択する
        if not binarize and not batch_norm:
            # StochasticLut 演算のみ
            try:
                core_creator = {
                    bb.DType.FP32: {
                        6: core.StochasticLut6_fp32.create,
                        5: core.StochasticLut5_fp32.create,
                        4: core.StochasticLut4_fp32.create,
                        2: core.StochasticLut2_fp32.create,
                    },
                    bb.DType.BIT: {
                        6: core.StochasticLut6_bit.create,
                        5: core.StochasticLut5_bit.create,
                        4: core.StochasticLut4_bit.create,
                        2: core.StochasticLut2_bit.create,
                    },
                }[bin_dtype][N]
            except KeyError:
                raise TypeError("unsupported")

            core_model  = core_creator(output_shape, connection, seed)
        
        elif binarize:
            # 条件が揃えば BatchNorm と 二値化を一括演算
            try:
                core_creator = {
                    bb.DType.FP32: {
                        6: core.DifferentiableLut6_fp32.create,
                        5: core.DifferentiableLut5_fp32.create,
                        4: core.DifferentiableLut4_fp32.create,
                        2: core.DifferentiableLut2_fp32.create,
                    },
                    bb.DType.BIT: {
                        6: core.DifferentiableLut6_bit.create,
                        5: core.DifferentiableLut5_bit.create,
                        4: core.DifferentiableLut4_bit.create,
                        2: core.DifferentiableLut2_bit.create,
                    },                    
                }[bin_dtype][N]
            except KeyError:
                raise TypeError("unsupported")
            
            core_model = core_creator(output_shape, batch_norm, connection, momentum, gamma, beta, seed)
        
        else:
            # 個別演算
            try:
                core_creator = {
                    bb.DType.FP32: {
                        6: core.DifferentiableLutDiscrete6_fp32.create,
                        5: core.DifferentiableLutDiscrete5_fp32.create,
                        4: core.DifferentiableLutDiscrete4_fp32.create,
                        2: core.DifferentiableLutDiscrete2_fp32.create,
                    },
                    bb.DType.BIT: {
                        6: core.DifferentiableLutDiscrete6_bit.create,
                        5: core.DifferentiableLutDiscrete5_bit.create,
                        4: core.DifferentiableLutDiscrete4_bit.create,
                        2: core.DifferentiableLutDiscrete2_bit.create,
                    },                    
                }[bin_dtype][N]
            except KeyError:
                raise TypeError("unsupported")
            
            core_model = core_creator(output_shape, batch_norm, binarize, connection, momentum, gamma, beta, seed)

        super(DifferentiableLut, self).__init__(core_model=core_model, input_shape=input_shape, name=name)

    def W(self):
        """重み行列取得
        
            コピーではなくスライス参照を得ており、本体の値を書き換え可能

        Returns:
            W (Tensor): 重み行列を指すTensor
        """
        return bb.Tensor.from_core(self.get_core().W())
    
    def dW(self):
        """重みの勾配行列取得

            コピーではなくスライス参照を得ており、本体の値を書き換え可能

        Returns:
            W (Tensor): 重みの勾配を指すTensor
        """
        return bb.Tensor.from_core(self.get_core().dW())


class BinaryLut(SparseModel):
    """バイナリLUTモデル

       一般的なFPGAのLUTと同等の機能をするモデル。
       学習能力はなく、他のモデルで学習した結果をインポートしてモデル評価を行うためのもの
        
    Args:
        output_shape (List[int]): 出力のシェイプ
        connection(str): 結線ルールを 'random', 'serial', 'depthwise' から指定可能(未実装)
        N (int): LUTの入力数
        seed (int): 変数初期値などの乱数シード
        fw_dtype (DType)): forwardの型を bb.DType.FP32 と bb.DType.BIT から指定
    """
    
    def __init__(self, output_shape, *, input_shape=None,
                    connection='random', seed=1, name=None, N=6, fw_dtype=bb.DType.FP32, bw_dtype=bb.DType.FP32):
        
        try:
            core_creator = {
                bb.DType.FP32: {
                    6: core.BinaryLut6_fp32.create,
                    5: core.BinaryLut5_fp32.create,
                    4: core.BinaryLut4_fp32.create,
                    2: core.BinaryLut2_fp32.create,
                },
                bb.DType.BIT: {
                    6: core.BinaryLut6_bit.create,
                    5: core.BinaryLut5_bit.create,
                    4: core.BinaryLut4_bit.create,
                    2: core.BinaryLut2_bit.create,
                },
            }[fw_dtype][N]
        except KeyError:
            raise TypeError("unsupported")

        core_model  = core_creator(output_shape, connection, seed)
        
        super(BinaryLut, self).__init__(core_model=core_model, input_shape=input_shape, name=name)

    def import_layer(self, leyaer):
        """他のモデルからからインポート

            インポート元は入出力が同じ形状をしている必要があり、デジタル値の入力に対して
            出力を 0.5 を閾値として、バイナリテーブルを構成して取り込む

        Args:
            leyaer (Model): インポート元のモデル
        """
        self.get_core().import_layer(leyaer.get_core())

    @staticmethod
    def from_sparse_model(layer, *, fw_dtype=bb.DType.FP32):
        """他のモデルを元に生成

            インポート元は入出力が同じ形状をしている必要があり、デジタル値の入力に対して
            出力を 0.5 を閾値として、バイナリテーブルを構成して取り込む

        Args:
            leyaer (Model): インポート元のモデル
        """
        N = layer.get_core().get_node_connection_size(0)
        new_model = BinaryLut(output_shape=layer.get_output_shape(), input_shape=layer.get_input_shape(),
                                 N=N, fw_dtype=fw_dtype)
        new_model.import_layer(layer)
        return new_model

# ------- フィルタ --------


class ConvolutionIm2Col(Model):
    """ConvolutionIm2Col class
       畳み込みの lowering における im2col 層
    """

    def __init__(self, filter_size=(1, 1), stride=(1, 1), *,
                        padding='valid', border_mode='reflect_101', border_value=0.0,
                        input_shape=None, name=None, fw_dtype=bb.DType.FP32, bw_dtype=bb.DType.FP32):

        try:
            core_creator = {
                bb.DType.FP32: core.ConvolutionIm2Col_fp32.create,
                bb.DType.BIT:  core.ConvolutionIm2Col_bit.create,
            }[fw_dtype]
        except KeyError:
            raise TypeError("unsupported")

        core_model = core_creator(filter_size[0], filter_size[1], stride[0], stride[1], padding, border_mode)
        
        super(ConvolutionIm2Col, self).__init__(core_model=core_model, input_shape=input_shape, name=name)


class ConvolutionCol2Im(Model):
    """ConvolutionCol2Im class
       畳み込みの lowering における col2im 層
    """

    def __init__(self, output_size=(1, 1), *, input_shape=None, name=None, fw_dtype=bb.DType.FP32, bw_dtype=bb.DType.FP32):
        try:
            core_creator = {
                bb.DType.FP32: core.ConvolutionCol2Im_fp32.create,
                bb.DType.BIT:  core.ConvolutionCol2Im_bit.create,
            }[fw_dtype]
        except KeyError:
            raise TypeError("unsupported")

        core_model = core_creator(output_size[0], output_size[1])
        
        super(ConvolutionCol2Im, self).__init__(core_model=core_model, input_shape=input_shape, name=name)


class Convolution2d(Sequential):
    """Convolution class
        Lowering による畳み込み演算をパッキングするクラス

        sub_layer で指定した演算レイヤーを畳み込み計算するためのモデル
        例えば sub_layer に DenseAffineレイヤーを指定すると一般的なCNN用の畳み込み層となるが、
        BinaryBrain ではここに DifferentiableLut モデルを組み合わせて作った複合レイヤーを
        指定することでFPGA化に適した畳み込み層を学習させることができる。

        sub_layer で指定したサブレイヤーが im2col と col2im で挟み込まれ、一般に
        Lowering と呼ばれる方法で畳み込み演算が実行される

    Args:
        sub_layer (Model): 畳み込みを行うサブレイヤー(このレイヤが im2col と col2im で挟み込まれる)
        filter_size ((int, int)): 2次元のタプルでフィルタサイズを指定する
        stride ((int, int)): 2次元のタプルでストライドサイズを指定する
        batch_norm (bool): BatchNormalization を有効にするか
        padding (str)): パディングの方法を 'valid' と 'same' で指定する
        border_mode (Border)): 'same' 時のボーダー処理を指定する
        border_value (float): 'same' 時のボーダー処理が CONSTANT の場合にパディング値を指定する
        fw_dtype (DType)): forwarする型を bb.DType.FP32 と bb.DType.BIT から指定
    """

    def __init__(self, sub_layer, filter_size=(1, 1), stride=(1, 1), *, input_shape=None,
                        padding='valid', border_mode='reflect_101', border_value=0.0,
                        name=None, fw_dtype=bb.DType.FP32, bw_dtype=bb.DType.FP32):
        super(Convolution2d, self).__init__()
        
        try:
            self.core_creator = {
                bb.DType.FP32: core.Convolution2d_fp32.create,
                bb.DType.BIT:  core.Convolution2d_bit.create,
            }[fw_dtype]
        except KeyError:
            raise TypeError("unsupported")
        
        self.deny_flatten = True
        self.name         = name
        self.input_shape  = input_shape
        self.filter_size  = filter_size
        self.stride       = stride
        self.padding      = padding
        self.border_mode  = border_mode
        self.border_value = border_value
        self.fw_dtype     = fw_dtype
        self.bw_dtype     = bw_dtype
        
        self.im2col       = ConvolutionIm2Col(filter_size=filter_size, stride=stride,
                                padding=padding, border_mode=border_mode, border_value=border_value,
                                fw_dtype=fw_dtype, bw_dtype=bw_dtype)
        self.sub_layer    = sub_layer
        self.col2im       = None  # 後で決定
    
    def send_command(self, command, send_to="all"):
        self.im2col.send_command(command=command, send_to=send_to)
        self.sub_layer.send_command(command=command, send_to=send_to)
        self.col2im.send_command(command=command, send_to=send_to)
    
    def get_core(self):
        core_model = self.core_creator(self.im2col.get_core(), self.sub_layer.get_core(), self.col2im.get_core())
        if self.name is not None:
            core_model.set_name(self.name)
        return core_model
    
    def get_sub_layer(self):
        return self.sub_layer
    
    def set_input_shape(self, shape):
        self.input_shape = shape
        
        # 出力サイズ計算
        input_c_size = shape[0]
        input_h_size = shape[1]
        input_w_size = shape[2]
        if self.padding == "valid":
            output_h_size = ((input_h_size - self.filter_size[0] + 1) + (self.stride[0] - 1)) // self.stride[0]
            output_w_size = ((input_w_size - self.filter_size[1] + 1) + (self.stride[1] - 1)) // self.stride[1]
        elif self.padding == "same":
            output_h_size = (input_h_size + (self.stride[0] - 1)) // self.stride[0]
            output_w_size = (input_w_size + (self.stride[1] - 1)) // self.stride[0]
        else:
            raise ValueError("illegal padding value")
        
        self.col2im = ConvolutionCol2Im(output_size=[output_h_size, output_w_size], fw_dtype=self.fw_dtype, bw_dtype=self.bw_dtype)
        
        super(Convolution2d, self).set_model_list([self.im2col, self.sub_layer, self.col2im])
        
        return super(Convolution2d, self).set_input_shape(shape)


class MaxPooling(Model):
    """MaxPooling class

    Args:
        filter_size ((int, int)): 2次元のタプルでフィルタサイズを指定する
        fw_dtype (DType)): forwarする型を bb.DType.FP32 と bb.DType.BIT から指定
    """

    def __init__(self, filter_size=(2, 2), *, input_shape=None, name=None, fw_dtype=bb.DType.FP32, bw_dtype=bb.DType.FP32):
        try:
            core_creator = {
                bb.DType.FP32: core.MaxPooling_fp32.create,
                bb.DType.BIT:  core.MaxPooling_bit.create,
            }[fw_dtype]
        except KeyError:
            raise TypeError("unsupported")

        core_model = core_creator(filter_size[0], filter_size[1])

        super(MaxPooling, self).__init__(core_model=core_model, input_shape=input_shape, name=name)


class StochasticMaxPooling(Model):
    """StochasticMaxPooling class

        Stochastic 演算として OR 演算で Pooling 層を構成するモデル

    Args:
        filter_size ((int, int)): 2次元のタプルでフィルタサイズを指定する(現在2x2のみ)
        fw_dtype (DType)): forwarする型を bb.DType.FP32 と bb.DType.BIT から指定
    """

    def __init__(self, filter_size=(2, 2), *, input_shape=None, name=None, fw_dtype=bb.DType.FP32, bw_dtype=bb.DType.FP32):
        assert(len(filter_size)==2)

        if  filter_size[0]==2 and filter_size[1]==2:
            try:
                core_creator = {
                    bb.DType.FP32: core.StochasticMaxPooling2x2_fp32.create,
                    bb.DType.BIT:  core.StochasticMaxPooling2x2_bit.create,
                }[fw_dtype]
            except KeyError:
                raise TypeError("unsupported")
            
            core_model = core_creator()
        else:
            try:
                core_creator = {
                    bb.DType.FP32: core.StochasticMaxPooling_fp32.create,
                    bb.DType.BIT:  core.StochasticMaxPooling_bit.create,
                }[fw_dtype]
            except KeyError:
                raise TypeError("unsupported")
            
            core_model = core_creator(filter_size[0], filter_size[1])

        super(StochasticMaxPooling, self).__init__(core_model=core_model, input_shape=input_shape, name=name)


class UpSampling(Model):
    """UpSampling class

        畳み込みの逆方向にアップサンプリングを行うモデル

    Args:
        filter_size ((int, int)): 2次元のタプルでフィルタサイズを指定する(現在2x2のみ)
        fw_dtype (DType)): forwarする型を bb.DType.FP32 と bb.DType.BIT から指定
    """

    def __init__(self, filter_size=(2, 2), *, fill=True, input_shape=None, name=None, fw_dtype=bb.DType.FP32, bw_dtype=bb.DType.FP32):

        try:
            core_creator = {
                bb.DType.FP32: core.UpSampling_fp32.create,
                bb.DType.BIT:  core.UpSampling_bit.create,
            }[fw_dtype]
        except KeyError:
            raise TypeError("unsupported")
        
        core_model = core_creator(filter_size[0], filter_size[1], fill)

        super(UpSampling, self).__init__(core_model=core_model, input_shape=input_shape, name=name)



# ------- 活性化 --------

class Binarize(Model):
    """Binarize class

    2値化(活性化層)
    backward は hard-tanh となる

    Args:
        bin_dtype (DType)): バイナリ型を bb.DType.FP32 と bb.DType.BIT から指定
    """


    def __init__(self, *, input_shape=None, name=None, bin_dtype=bb.DType.FP32):
        try:
            core_creator = {
                bb.DType.FP32: core.Binarize_fp32.create,
                bb.DType.BIT:  core.Binarize_bit.create,
            }[bin_dtype]
        except KeyError:
            raise TypeError("unsupported")

        core_model = core_creator()

        super(Binarize, self).__init__(core_model=core_model, input_shape=input_shape, name=name)



class Sigmoid(Model):
    """Sigmoid class

       Sigmoid 活性化層
       send_command で "binary true" とすることで、Binarize に切り替わる
       多値で学習を進めて、途中から Binarize に切り替える実験などが可能である
    """
    def __init__(self, *, input_shape=None, name=None, dtype=bb.DType.FP32):

        try:
            core_creator = {
                bb.DType.FP32: core.Sigmoid.create,
            }[dtype]
        except KeyError:
            raise TypeError("unsupported")

        core_model = core_creator()

        super(Sigmoid, self).__init__(core_model=core_model, input_shape=input_shape, name=name)


class ReLU(Model):
    """ReLU class

       ReLU 活性化層
       send_command で "binary true" とすることで、Binarize に切り替わる
       多値で学習を進めて、途中から Binarize に切り替える実験などが可能である
    """
    def __init__(self, *, input_shape=None, name=None, dtype=bb.DType.FP32):

        try:
            core_creator = {
                bb.DType.FP32: core.ReLU.create,
            }[dtype]
        except KeyError:
            raise TypeError("unsupported")

        core_model = core_creator()

        super(ReLU, self).__init__(core_model=core_model, input_shape=input_shape, name=name)


class HardTanh(Model):
    """HardTanh class

       HardTanh 活性化層
       send_command で "binary true" とすることで、Binarize に切り替わる
       多値で学習を進めて、途中から Binarize に切り替える実験などが可能である
    """
    def __init__(self, *, input_shape=None, name=None, dtype=bb.DType.FP32):

        try:
            core_creator = {
                bb.DType.FP32: core.HardTanh.create,
            }[dtype]
        except KeyError:
            raise TypeError("unsupported")

        core_model = core_creator()

        super(HardTanh, self).__init__(core_model=core_model, input_shape=input_shape, name=name)



# ------- 補助モデル --------

class BatchNormalization(Model):
    """BatchNormalization class

    Args:
        momentum (float): 学習モーメント
        gamma (float): gamma 初期値
        beta (float): beta 初期値
        fix_gamma (bool): gamma を固定する(学習させない)
        fix_beta (bool): beta を固定する(学習させない)
        bin_dtype (DType)): バイナリ型を bb.DType.FP32 と bb.DType.BIT から指定
    """

    def __init__(self, *, input_shape=None, momentum=0.9, gamma=1.0, beta=0.0,
                        fix_gamma=False, fix_beta=False, name=None, dtype=bb.DType.FP32):
        try:
            core_creator = {
                bb.DType.FP32: core.BatchNormalization.create,
            }[dtype]
        except KeyError:
            raise TypeError("unsupported")

        core_model = core_creator(momentum, gamma, beta, fix_gamma, fix_beta)

        super(BatchNormalization, self).__init__(core_model=core_model, input_shape=input_shape, name=name)


class Dropout(Model):
    """Dropout class

    Args:
        rate (float): Drop率
        seed (int): 乱数シード
        fw_dtype (DType): forwardの型を bb.DType.FP32 と bb.DType.BIT から指定
    """

    def __init__(self, *, rate=0.5, input_shape=None, seed=1, name=None, fw_dtype=bb.DType.FP32, bw_dtype=bb.DType.FP32):
        try:
            core_creator = {
                bb.DType.FP32: core.Dropout.create,
                bb.DType.FP32: core.Dropout.create,
            }[fw_dtype]
        except KeyError:
            raise TypeError("unsupported")

        core_model = core_creator(rate, seed)

        super(Dropout, self).__init__(core_model=core_model, input_shape=input_shape, name=name)


class Shuffle(Model):
    """Shuffle class

        所謂 ShuffleNet のようなシャッフルを行うモデル
        入力ノードが shuffle_unit 個のグループに分割されるようにシャッフルする


    Args:
        shuffle_unit (int): シャッフルする単位
    """

    def __init__(self, shuffle_unit, *, output_shape=[], input_shape=None, name=None, bit_dtype=bb.DType.FP32, real_dtype=bb.DType.FP32):

        try:
            core_creator = {
                bb.DType.FP32: core.Shuffle.create,
                bb.DType.BIT:  core.Shuffle.create,
            }[bit_dtype]
        except KeyError:
            raise TypeError("unsupported")
        
        core_model = core_creator(shuffle_unit, output_shape)

        super(Shuffle, self).__init__(core_model=core_model, input_shape=input_shape, name=name)



# ------- その他 --------


def get_model_list(net, flatten:bool =False):
    ''' Get model list from networks
        ネットから構成するモデルのリストを取り出す
    
        Args:
            net     (Model): 検索するパス
            flatten (bool): 階層をフラットにするかどうか
        Returns:
            list of models
    '''
    
    if  type(net) is not list:
        net = [net]
    
    if not flatten:
        return net
    
    def flatten_list(in_list, out_list):
        for model in in_list:
            if hasattr(model, 'get_model_list') and not hasattr(model, 'deny_flatten'):
                flatten_list(model.get_model_list(), out_list)
            else:
                out_list.append(model)
    
    out_list = []
    flatten_list(net, out_list)
    
    return out_list
