

import numpy as np
import gurobipy as gp

import pprint as pp

import copy

from collections import defaultdict


def dispBoard(board):
    '''
    数独盤面(二次元配列)を見やすいように可視化

         9  2  6  |  5  7  1  |  4  8  3
         3  5  1  |  4  8  6  |  2  7  9
         8  7  4  |  9  2  3  |  5  1  6
        ----------+-----------+----------
         5  8  2  |  3  6  7  |  1  9  4
         1  4  9  |  2  5  8  |  3  6  7
         7  6  3  |  1  9  4  |  8  2  5
        ----------+-----------+----------
         2  3  8  |  7  4  9  |  6  5  1
         6  1  7  |  8  3  5  |  9  4  2
         4  9  5  |  6  1  2  |  7  3  8

    '''

    Nsize = len(board)
    gsize = int(np.sqrt(Nsize))
    for idx, row in enumerate(board):

        out = ""
        for jdx, col in enumerate(row):

            col = "-" if col==0 else str(col)
            out += " %s "%col

            if jdx % gsize == gsize-1 and jdx<Nsize-1:
                out += " | "
        print(out)

        if idx % gsize == gsize-1 and idx<Nsize-1:
            out = ""

            for jdx, col in enumerate(row):
                out += "---"
                if jdx % gsize == gsize-1 and jdx<Nsize-1:
                    out += "-+-"
            print(out)


    print("\n")




class SudokuModel(gp.Model):
    '''
    NxN 数独数理モデルクラス

        数独の盤面を数理モデルとして定義し、探索を行うクラス

    Input:
        board_in: 数独の盤面を示す二次元配列
            盤面のサイズはN x N(Nは平方数)とする

    '''


    def __init__(self, board_in):

        super().__init__()

        Nsize = len(board_in)
        gsize = int(np.sqrt(Nsize))

        print(f'############## Sudoku Solver {Nsize} x {Nsize} ###############')

        print('\n')

        self._board_in = board_in


        '''数理モデル定義部(ここから)'''

        #HINT 決定変数X[i,j] = n
        #HINT マス(i:行,j:列) に数字nを配置する場合に1, しない場合に0

        x = defaultdict(int)
        for i, init_i in enumerate(board_in):
            for j, initVal in enumerate(init_i):
                #HINT マス(i,j)の値がゼロ→「未定義」として、1～Nいずれかの値が入る前提で変数化
                if initVal == 0:
                    for n in range(1, Nsize+1):
                        x[(i,j,n)] = self.addVar(vtype = gp.GRB.BINARY, name = f'x[{i},{j},{n}]')
                #HINT マス(i,j)の値がゼロでない(initVal)
                #HINT マス(i,j)には値initValが入る(i,j, initVal)に対して、値1(int)を代入
                #HINT n!=initValは1にならないことが確定しているため、(i,j,n)に組み合わせは変数を定義しない。
                #HINT ただし、defaultdict(int)としているため、アクセスした場合は値ゼロを返す
                else:
                    x[(i,j,initVal)] = 1

        self.update()

        self._x = x

        #HINT 制約G
        #HINT 1マス(1Grid)につき値は1つしか値は入らない
        for i in range(Nsize):
            for j in range(Nsize):
                xsum = gp.quicksum(x[i,j,n] for n in range(1, Nsize+1))
                self.addConstr(xsum == 1, name = f'G[r={i},c={j}]')

        #HINT 制約H, V
        #HINT 各数字は、各行内(H)および各列内(V)では、1回ずつしか登場しない
        for n in range(1, Nsize + 1):
            for i in range(Nsize):
                #HINT 数値nが列内に登場する回数
                xsumH = gp.quicksum(x[i,j,n] for j in range(Nsize))
                self.addConstr(xsumH == 1, name = f'V[r={j},n={n}]')

                #HINT 数値nが行内に登場する回数(i,j逆転に注意)
                xsumV = gp.quicksum(x[j,i,n] for j in range(Nsize))
                self.addConstr(xsumV == 1, name = f'V[c={j},n={n}]')

        #HINT 制約A:#ANS-1
        #HINT 各数字はn x nの正方形であらわされる各エリア内で1回ずつしか登場しない#ANS-1
        for n in range(1, Nsize + 1):#ANS-1
            for ai in range(gsize):#ANS-1
                for aj in range(gsize):#ANS-1
                    xsumA = gp.quicksum(#ANS-1
                        x[(ii + ai * gsize, jj + aj * gsize ,n)]#ANS-1
                        for ii in range(gsize) for jj in range(gsize)#ANS-1
                    )#ANS-1
                    self.addConstr(xsumA == 1, name = f'A[a=({ai},{aj}),n={n}]')#ANS-1


        '''数理モデル定義部(ここまで)'''



    def getResult(self):

        '''
        探索・結果出力
            数独-数理モデルの探索を行い、


        Output:
            1. ステータスコード
                解ありの場合: True
                解なしの場合: False
            2. 数独の盤面

                解ありの場合: 結果を示す二次元配列
                解なしの場合: ALL0の二次元配列


            ステータス値=True および結果の盤面を二次元配列として出力する
            数独数理モデルが解なしの場合、
            ステータス値=False および空の配列を出力する
        '''

        '''探索実行'''
        self.optimize()

        #HINT 解なし場合
        if self.Status == gp.GRB.INFEASIBLE:
            Nsize = len(self._board_in)
            board_out = [[0] * Nsize] * Nsize
            status = False
        else:
        #HINT 解ありの場合
            status = True
            board_out = copy.deepcopy(self._board_in)
            for (i,j,n),xv in self._x.items():
                #HINT xvには、int値(1 or 0) もしくは gurobiVar(0,1)の値が入る。#HINT1
                #HINT int場合.Xにて値取得不可。+LinExprを足し合わせることでgetValue()で値取得できる#HINT1
                #HINT 決定変数Xが未定義のi,jについては入力盤面の値をそのまま踏襲するため、更新しない。#HINT2
                if (xv + gp.LinExpr()).getValue() > 0.5:
                    board_out[i][j] = n

        return status, board_out



    def phbtExistingSolution(self, sol):
        '''
        入力された解と同じ解を得ることを禁止する制約

        Input:
            sol
            数独の解を示す二次元配列
        '''

        pass

        '''実装を追加すること(Exersize2)'''


        #解のサイズ: NxN二次元配列のため、N^2 #ANS-2
        Ssize = len(sol)**2#ANS-2


        xsum = gp.quicksum(#ANS-2
            self._x[idx,jdx,col]#ANS-2
            for idx, row in enumerate(sol)#ANS-2
            for jdx, col in enumerate(row)#ANS-2
        )#ANS-2

        print(f"既知解禁止制約: {self._solCnt}回目")#ANS-2

        self.addConstr(xsum <= Ssize-1, name = f'ihbtSol[{self._solCnt}]')#ANS-2






##################################################


def exercise1():
    '''
    演習1: 不完全なモデル

        目的
            数理モデル定義部実装を修正することで
            正しい数理モデルが生成できるようにすること
        前提条件
            数独ソルバとして不完全な数理モデル(※)が実装済み。
            本来は解なしとなるべき問題が解ありとなってしまう。
            ※ 数理モデル定義部に意図的なバグor実装漏れあり


        OK条件
            入力盤面に対する求解結果が解なし(result==False)となること

    '''


    #問題定義
    # N x N(平方数)の数独問題をpython 2次元配列で記載。
    # 空白は値ゼロとする。

    #FIXME ↓をベースに改編済みの盤面。
    ex1_in = [
        [5, 3, 0, 0, 7, 0, 0, 0, 0],
        [6, 0, 0, 1, 9, 5, 0, 0, 0],
        [0, 9, 8, 0, 0, 0, 0, 6, 0],
        [8, 0, 0, 0, 6, 0, 5, 0, 3],
        [4, 0, 0, 8, 0, 3, 0, 0, 1],
        [7, 0, 0, 0, 2, 0, 0, 0, 6],
        [0, 6, 0, 0, 0, 0, 2, 8, 0],
        [0, 0, 0, 4, 1, 9, 0, 0, 5],
        [0, 0, 0, 0, 8, 0, 0, 7, 9],
    ]


    # FIXME ↑の編集元
    # ex1_in = [#FIXME
    #     [5, 3, 0, 0, 7, 0, 0, 0, 0],#FIXME
    #     [6, 0, 0, 1, 9, 5, 0, 0, 0],#FIXME
    #     [0, 9, 8, 0, 0, 0, 0, 6, 0],#FIXME
    #     [8, 0, 0, 0, 6, 0, 0, 0, 3],#FIXME
    #     [4, 0, 0, 8, 0, 3, 0, 0, 1],#FIXME
    #     [7, 0, 0, 0, 2, 0, 0, 0, 6],#FIXME
    #     [0, 6, 0, 0, 0, 0, 2, 8, 0],#FIXME
    #     [0, 0, 0, 4, 1, 9, 0, 0, 5],#FIXME
    #     [0, 0, 0, 0, 8, 0, 0, 7, 9],#FIXME
    # ]#FIXME


    ##################################


    model = SudokuModel(board_in = ex1_in)
    result, ex1_out = model.getResult()

    print("\n")
    print("#"*20)
    print("[Exercise1]: Input")
    print("#"*20)

    #Input盤面の可視化
    dispBoard(ex1_in)

    print("\n")
    print("#"*20)
    print("[Exercise1]: Output")
    print("#"*20)



    try:
        assert result == False
    except:
        print("\nExercize1: NG(解ありになってしまう)\n")



        dispBoard(ex1_out)
        print("\n")
        exit()


#################################################################

'''
演習2: 複数解の列挙


目的
    複数パタンの解がある数独の盤面に対して
    その解をすべて列挙する

前提条件

    探索を繰り返し実行するwhileループを実装済み
        (1)探索n回目には、[n-1回目までの解を禁止する制約]を追加
        (2)すべての解が出尽くした時点で(1)により解なしとなる、whileループを抜ける


演習内容
    [N-1回目までの解を禁止する制約]の実現手段(制約式など)を検討して
    phbtExistingSolutionメソッド内部に実装すること

OK条件


'''



ex2Ans = set([
    '926571483351486279874923516582367194149258367763149825238794651617835942495612738',
    '926571483351486279874923516582367194149258367763194825238749651617835942495612738'
    ]
)


def exercise2():

    '''
    解が二通りある数独の盤面
        https://sudokuplus.net/2022/can-sudoku-have-two-solutions/
    '''


    ex2_in =[
        [9, 2, 6, 5, 7, 1, 4, 8, 3],
        [3, 5, 1, 4, 8, 6, 2, 7, 9],
        [8, 7, 4, 9, 2, 3, 5, 1, 6],
        [5, 8, 2, 3, 6, 7, 1, 9, 4],
        [1, 4, 9, 2, 5, 8, 3, 6, 7],
        [7, 6, 3, 1, 0, 0, 8, 2, 5],
        [2, 3, 8, 7, 0, 0, 6, 5, 1],
        [6, 1, 7, 8, 3, 5, 9, 4, 2],
        [4, 9, 5, 6, 1, 2, 7, 3, 8]
    ]
    #初回

    print("\n")
    print("#"*20)
    print("[Exercise3]: Input")
    print("#"*20)

    dispBoard(ex2_in)


    model = SudokuModel(board_in = ex2_in)
    model._solCnt = 0
    model.params.LogToConsole = 0



    results =[]
    result = True
    while result and model._solCnt < 30:

        #2回目以降: 既知禁止制約を追加
        if model._solCnt > 0:
            #
            model.phbtExistingSolution(sol = ex2_out)
        result, ex2_out = model.getResult()

        if result:
            model._solCnt += 1

            print("\n")
            print("#"*20)
            print("[Exercise2]: Output-%d"%model._solCnt)
            print("#"*20)

            #出力盤面(二次元配列)を文字列に変換
            outStr = "".join(np.vectorize(str)(ex2_out).flatten())
            results.append(outStr)
            dispBoard(ex2_out)#盤面の可視化

    print("\n解なし\n")
    print(f"[Exercise2]: 解の数 = {model._solCnt}\n")

    assert set(results) == ex2Ans, f"解が期待値と不一致 {ex2Ans} != {results}"


    print(f"[Exercise2]: 解も完全一致\n")

if __name__ == '__main__':


    exercise1()

    input("\nEx1結果: OK(期待通りに解なし)\n\n")

    exercise2()
