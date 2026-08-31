# 精算統計模型

研究所層級之迴歸與統計學習課程，14 週授課、每週 3 節（50 分鐘 × 3），共 42 節；
另加期中、期末考各一次。

課程以線性模型的矩陣理論為骨幹：一律先以 $k$ 個解釋變數推導，簡單線性迴歸（$k = 1$）
作為特例處理，不另立單元。SOA **Exam SRM** 指定閱讀範圍為本課程的主要參考來源之一，
其全部指定章節均涵蓋於課程中（對照見文末附錄）；此外另加授 SRM 範圍外但學理上必要的
主題：拔靴法、凸規劃與支持向量機、類神經網路。

## 教科書

- [James, G., Witten, D., Hastie, T., Tibshirani, R., 2021. An Introduction to Statistical Learning: With Applications in R. 2nd ed., Springer. (ISLR)](https://www.statlearning.com/)
- Frees, E. W., 2010. Regression Modeling with Actuarial and Financial Applications. Cambridge University Press, New York, 2010. (FREES)
- Lander, J. P., 2017. R for Everyone. Addison-Wesley, Boston, 2nd ed.
- Healy, K., 2019. Data Visualization: A Practical Introduction. Princeton University Press, Princeton, NJ.
- 教師編纂講義。

### 課程講義

| &nbsp;<a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit01.pdf">01</a>&nbsp; | &nbsp;<a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit02.pdf">02</a>&nbsp; | &nbsp;<a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit03.pdf">03</a>&nbsp; | &nbsp;<a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit04.pdf">04</a>&nbsp; | &nbsp;<a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit05.pdf">05</a>&nbsp; | &nbsp;<a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit06.pdf">06</a>&nbsp; | &nbsp;<a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit07.pdf">07</a>&nbsp; | &nbsp;<a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit08.pdf">08</a>&nbsp; | &nbsp;<a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit09.pdf">09</a>&nbsp; | &nbsp;<a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit10.pdf">10</a>&nbsp; | &nbsp;<a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit11.pdf">11</a>&nbsp; | &nbsp;<a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit12.pdf">12</a>&nbsp; | &nbsp;<a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit13.pdf">13</a>&nbsp; | &nbsp;<a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit14.pdf">14</a>&nbsp; |

### 數學先備知識

| &nbsp;<a href="https://github.com/chang-ye-tu/asm/blob/master/note/prereq.pdf">Mathematical Prerequisites</a>&nbsp; |

課程所需之分析、線性代數與測度論機率，集中於此單一來源，並全部給出證明：

* **第一部 分析**（不預設實分析背景，自 $\Real$ 之完備性起）：上／下確界、
  Bolzano–Weierstrass、Heine–Borel、Rolle 與均值定理、**積分號下微分**、
  極限與半連續、Taylor 定理、凸性與分離超平面、**凸規劃**（Lagrange 對偶、
  弱對偶、Slater 條件下之強對偶、KKT 條件與互補鬆弛）。
* **第二部 線性代數**：秩—零度、**跡**、正交投影、**譜定理**、正定與對稱平方根、
  冪等矩陣（tr = rank）、Schur 補與 Sherman–Morrison、**奇異值分解**、
  **算子範數與條件數**、矩陣微分與連鎖律。
* **第三部 測度論機率**：期望值與不等式、Borel–Cantelli、條件期望（$L^2$ 投影）、
  多變量常態、$\chi^2$／$t$／$F$ 分配、收斂模式、特徵函數、Lévy 連續性定理、
  Portmanteau 與連續映射定理、Slutsky 定理、Lindeberg–Feller 中央極限定理、delta 法。
* **第四部**：課程中實際引用的結果。

全書僅假設 $\Real$ 之完備性與 Lebesgue 積分之四個收斂定理（單調、Fatou、控制、
Fubini–Tonelli）；其餘一律推導。

### 補充講義

| &nbsp;<a href="https://github.com/chang-ye-tu/mva/blob/master/note/clm.pdf">Classical Linear Models</a>&nbsp; | &nbsp;<a href="https://github.com/chang-ye-tu/mva/blob/master/note/mc.pdf">Matrix Calculus</a>&nbsp; | &nbsp;<a href="https://github.com/chang-ye-tu/mva/blob/master/note/mlm.pdf">Modern Linear Models</a>&nbsp; |

Unit 2、3 的定理與證明取自 **CLM**；Unit 2 用到的微分工具取自 **MC**。
**MLM** 為非漸近高維理論，供延伸閱讀。

### 考題演練

<a href="https://github.com/chang-ye-tu/asm/blob/master/srm/srm.pdf">SOA Exam SRM 官方範例試題與詳解（重排版）</a>（71 題，每題後緊接該題解答）。

## 評分標準

- 期中考（40%）11/04 — 範圍 Unit 1–8
- 期末考（40%）12/23 — 範圍 Unit 9–14
- 平時成績（20%）

兩次考試均分兩部分：第一部分為五選一單選題（60 分），
第二部分為計算與證明題，須交代過程（40 分）。

## 授課時程

| 週次 | 上課時間 | 課程進度 | 指定閱讀 |
|:--:|:--|:--|:--|
| 1 | 09/09 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit01.pdf">**Unit 1** 統計學習</a><br>1.1 何謂統計學習：迴歸函數、可化約與不可化約誤差<br>1.2 模型準確度；貝氏分類器與 KNN<br>1.3 偏誤—變異數分解；重抽樣：LOOCV、*k*-fold CV、拔靴法 | ISLR 2、5.1–5.3<br>FREES 1 |
| 2 | 09/16 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit02.pdf">**Unit 2** 多元迴歸（一）：矩陣理論</a><br>2.1 正規方程式、帽子矩陣、正交投影、槓桿值<br>2.2 不偏性、var(**b**)、Gauss–Markov 定理、σ² 之估計<br>2.3 常態下的精確推論；配適度；**特例 *k*=1**：*r*、*R*²=*r*²、CAPM | FREES 2、3.1–3.3<br>ISLR 3.1–3.2<br>CLM 1–6 |
| 3 | 09/23 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit03.pdf">**Unit 3** 多元迴歸（二）：推論與詮釋</a><br>3.1 單一與多個係數之推論：*t*、一般線性假設、額外平方和<br>3.2 信賴區間與預測區間；特殊解釋變數：二元、類別、交互作用<br>3.3 FWL 定理、遺漏變數偏誤、迴歸結果的詮釋 | FREES 3.4–3.5、6.1<br>ISLR 3.3<br>CLM 7–9 |
| 4 | 09/30 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit04.pdf">**Unit 4** 迴歸診斷</a><br>4.1 迭代式建模；殘差分析、標準化與學生化殘差<br>4.2 具影響力的點：槓桿值、Cook's D、DFFITS／DFBETAS<br>4.3 共線性與 VIF；異質變異數、穩健標準誤與加權最小平方 | FREES 5.1、5.3–5.5、5.7<br>ISLR 3.3.3 |
| 5 | 10/07 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit05.pdf">**Unit 5** 變數選擇與維度縮減</a><br>5.1 最佳子集、前向／後向／逐步選擇<br>5.2 選擇準則：*C*<sub>p</sub>、AIC、BIC、調整 *R*²、概似比檢定<br>5.3 主成分分析初探；主成分迴歸（PCR）與偏最小平方（PLS） | FREES 5.2、5.6、6.2–6.3<br>ISLR 6.1、6.3、12.2 |
| 6 | 10/14 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit06.pdf">**Unit 6** 收縮法、高維度與 KNN</a><br>6.1 脊迴歸：閉式解、主成分收縮、有效自由度<br>6.2 Lasso 與彈性網；以 CV 選 λ<br>6.3 高維度下的迴歸；KNN 與 OLS 之比較；線性模型 R 實作 | ISLR 6.2、6.4–6.5、3.5–3.6 |
| 7 | 10/21 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit07.pdf">**Unit 7** 廣義線性模型（一）：類別反應變數</a><br>7.1 二元反應：線性機率模型、logistic 與 probit、勝算比<br>7.2 概似推論：MLE、Wald 與概似比檢定；分類指標與 ROC<br>7.3 名目反應（廣義 logit）；次序反應（累積 logit） | FREES 11 |
| 8 | 10/28 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit08.pdf">**Unit 8** 廣義線性模型（二）：計數與指數族</a><br>8.1 Poisson 迴歸、曝險量與 offset<br>8.2 過度離散、負二項、零膨脹與 hurdle 模型<br>8.3 線性指數族與連結函數；IRLS、偏差殘差、Tweedie 分布 | FREES 12、13 |
| 9 | **11/04** | **期中考**（Unit 1–8） | |
| 10 | 11/11 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit09.pdf">**Unit 9** 時間趨勢模型</a><br>9.1 時間趨勢的配適；以迴歸處理季節效應<br>9.2 定態性與隨機漫步；隨機漫步下的推論；差分濾波<br>9.3 預測績效評估；自我相關係數 | FREES 7、8.1 |
| 11 | 11/18 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit10.pdf">**Unit 10** 自迴歸模型與預測</a><br>10.1 AR(1) 與 AR(p)／MA(q)／ARIMA；偏自我相關；條件最小平方之大樣本性質、殘差診斷與 Ljung–Box、預測<br>10.2 移動平均與指數平滑；季節模型；單根檢定；ARCH／GARCH<br>10.3 決策樹入門：遞迴二元切割、迴歸樹 | FREES 8.2–8.6、9<br>ISLR 8.1.1 |
| 12 | 11/25 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit11.pdf">**Unit 11** 決策樹</a><br>11.1 成本複雜度剪枝；以 CV 選 α<br>11.2 分類樹：Gini 指標、熵、誤分類率<br>11.3 樹與線性模型之比較；決策樹 R 實作 | ISLR 8.1、8.3.1–8.3.2 |
| 13 | 12/02 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit12.pdf">**Unit 12** 集成方法</a><br>12.1 Bagging 與袋外誤差；變數重要性<br>12.2 隨機森林：去相關與 mtry<br>12.3 Boosting；集成方法 R 實作 | ISLR 8.2、8.3.3–8.3.4 |
| 14 | 12/09 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit13.pdf">**Unit 13** 非監督式學習</a><br>13.1 主成分分析：載荷、分數、解釋變異比例、陡坡圖<br>13.2 *K*-means 分群<br>13.3 階層式分群：樹狀圖、連結方式；非監督式學習 R 實作 | ISLR 12.1–12.2、12.4–12.5 |
| 15 | 12/16 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit14.pdf">**Unit 14** 凸規劃、支持向量機與類神經網路</a><br>14.1 Lagrange 對偶與 KKT 條件；最大間隔分類器<br>14.2 對偶 SVM 與支持向量；軟間隔與核方法<br>14.3 多層感知器與反向傳播；R 實作 | 教師編纂講義 |
| 16 | **12/23** | **期末考**（Unit 9–14） | |

## 講義編譯

```bash
cd note
python build.py            # 編譯全部 14 個單元與附錄
python build.py 03         # 只編譯 Unit 3
python build.py prereq     # 只編譯數學先備知識
python build.py --pkg-check # 只檢查 R 套件是否齊備
```

需要 `Rscript`、`xelatex`、`bibtex`、`pygmentize`。
講義為 knitr `.Rnw`，17pt／16:9 版面，投影與列印共用同一份 PDF。

`unit01.Rnw` 至 `unit14.Rnw` 與 `prereq.Rnw` 是權威來源；同名 `.tex`、`figs/`、
`Sweave.sty` 與 LaTeX 輔助檔均為可重建產物。README 直接連結的 PDF 刻意納入版本控制，
讓學生不必安裝完整工具鏈即可閱讀草稿。完整建置要求所有十五份來源存在、檢查每個
子程序的退出碼，並持續執行 XeLaTeX 至交叉引用收斂；請勿在同一工作目錄平行執行 build。

撰寫講義前請先閱讀 [`note/CONVENTIONS.md`](note/CONVENTIONS.md)：
體例原則、資料來源對照，以及已知的陷阱。

## 附錄：SRM 指定閱讀範圍對照

SOA Exam SRM 之全部指定章節均涵蓋於本課程，對照如下。

### ISLR

| Chapter | Sections | Excluded | 對應單元 |
|:--:|:--|:--|:--|
| 2 | 1–3 | — | Unit 1 |
| 3 | 1–6 | — | Unit 2、3、6 |
| 5 | 1, 3 | 5.3.4 | Unit 1 |
| 6 | 1–5 | — | Unit 5、6 |
| 8 | 1–3 | 8.2.4, 8.2.5, 8.3.5 | Unit 10、11、12 |
| 12 | 1–2, 4–5 | 12.5.2 | Unit 5、13 |

### FREES

| Chapter | Sections | 對應單元 |
|:--:|:--|:--|
| 1 | Background only | Unit 1 |
| 2 | 1–8 | Unit 2 |
| 3 | 1–5 | Unit 2、3 |
| 5 | 1–7 | Unit 4、5 |
| 6 | 1–3 | Unit 3、5 |
| 7 | 1–6 | Unit 9 |
| 8 | 1–4 | Unit 9、10 |
| 9 | 1–5 | Unit 10 |
| 11 | 1–6 | Unit 7 |
| 12 | 1–4 | Unit 8 |
| 13 | 1–6 | Unit 8 |

### 對應 SOA 命題主題

| SOA Topic | 對應單元 |
|:--|:--|
| 1. Basics of Statistical Learning | Unit 1 |
| 2. Linear Models | Unit 2–8 |
| 3. Time Series Models | Unit 9–10 |
| 4. Decision Trees | Unit 10–12 |
| 5. Unsupervised Learning Techniques | Unit 5、13 |
| （SRM 範圍外） | Unit 1（拔靴法）、Unit 4（穩健標準誤）、Unit 14 |

兩項容易誤讀之處：ISLR 第 5 章 SRM 僅指定 5.1 與 5.3，**§5.2 拔靴法不在其範圍內**，
本課程仍納入（bagging 需要）；第 8 章排除 8.2.4（BART）與 8.2.5，但 **8.2.3 boosting
在範圍內**。AIC、BIC 採 ISLR §6.1.3 之定義：
AIC = (RSS + 2d·σ̂²)/n，BIC = (RSS + ln(n)·d·σ̂²)/n。

## 授課教師

changytu @ o365.fcu.edu.tw
