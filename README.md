# 精算統計模型

涵蓋 SOA Exam SRM 與 PA 之機器學習 / 資料分析。  

## 教科書

- [James, G., Witten, D., Hastie, T., Tibshirani, R., 2021. An Introduction to Statistical Learning: With Applications in R. 2nd ed., Springer. (ISLR)](https://www.statlearning.com/)
- [Frees, E. W., 2010. Regression Modeling with Actuarial and Financial Applications. Cambridge University Press, New York, 2010. (FREES)](https://users.ssc.wisc.edu/~ewfrees/ActuarialRegression2009/)
  - [Data & Scripts](https://instruction.bus.wisc.edu/jfrees/jfreesbooks/Regression%20Modeling/BookWebDec2010/home.html)
- Lander, J. P., 2017. R for Everyone. Addison-Wesley, Boston, 2nd ed.
- Healy, K., 2019. Data Visualization: A Practical Introduction. Princeton University Press, Princeton, NJ.

<!--

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

-->

## 評分標準

- 期中考（40%）11/04
- 期末考（40%）12/23
- 平時成績（20%）

## 授課時程

| 日期 | 課程進度 |
|:--|:--|
| 09/09 | **Unit 1** Statistical Learning <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit01.pdf"><img src="https://img.shields.io/badge/PDF-B31B1B?logo=adobeacrobatreader&logoColor=white" alt="PDF"></a> <a href="https://colab.research.google.com/github/chang-ye-tu/asm/blob/master/colab/unit01.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"></a> |
| 09/16 | **Unit 2** Multiple Regression I: Matrix Theory <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit02.pdf"><img src="https://img.shields.io/badge/PDF-B31B1B?logo=adobeacrobatreader&logoColor=white" alt="PDF"></a> <a href="https://colab.research.google.com/github/chang-ye-tu/asm/blob/master/colab/unit02.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"></a> |
| 09/23 | **Unit 3** Multiple Regression II: Inference and Interpretation <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit03.pdf"><img src="https://img.shields.io/badge/PDF-B31B1B?logo=adobeacrobatreader&logoColor=white" alt="PDF"></a> <a href="https://colab.research.google.com/github/chang-ye-tu/asm/blob/master/colab/unit03.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"></a> |
| 09/30 | **Unit 4** Regression Diagnostics <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit04.pdf"><img src="https://img.shields.io/badge/PDF-B31B1B?logo=adobeacrobatreader&logoColor=white" alt="PDF"></a> <a href="https://colab.research.google.com/github/chang-ye-tu/asm/blob/master/colab/unit04.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"></a> |
| 10/07 | **Unit 5** Variable Selection and Dimension Reduction <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit05.pdf"><img src="https://img.shields.io/badge/PDF-B31B1B?logo=adobeacrobatreader&logoColor=white" alt="PDF"></a> <a href="https://colab.research.google.com/github/chang-ye-tu/asm/blob/master/colab/unit05.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"></a> |
| 10/14 | **Unit 6** Shrinkage, Nearest Neighbours and High Dimensions <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit06.pdf"><img src="https://img.shields.io/badge/PDF-B31B1B?logo=adobeacrobatreader&logoColor=white" alt="PDF"></a> <a href="https://colab.research.google.com/github/chang-ye-tu/asm/blob/master/colab/unit06.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"></a> |
| 10/21 | **Unit 7** Generalized Linear Models I: Categorical Responses <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit07.pdf"><img src="https://img.shields.io/badge/PDF-B31B1B?logo=adobeacrobatreader&logoColor=white" alt="PDF"></a> <a href="https://colab.research.google.com/github/chang-ye-tu/asm/blob/master/colab/unit07.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"></a> |
| 10/28 | **Unit 8** Generalized Linear Models II: Counts and the Exponential Family <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit08.pdf"><img src="https://img.shields.io/badge/PDF-B31B1B?logo=adobeacrobatreader&logoColor=white" alt="PDF"></a> <a href="https://colab.research.google.com/github/chang-ye-tu/asm/blob/master/colab/unit08.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"></a> |
| **11/04** | **Midterm exam** |
| 11/11 | **Unit 9** Modeling Trends <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit09.pdf"><img src="https://img.shields.io/badge/PDF-B31B1B?logo=adobeacrobatreader&logoColor=white" alt="PDF"></a> <a href="https://colab.research.google.com/github/chang-ye-tu/asm/blob/master/colab/unit09.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"></a> |
| 11/18 | **Unit 10** Autoregressive Models and Forecasting <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit10.pdf"><img src="https://img.shields.io/badge/PDF-B31B1B?logo=adobeacrobatreader&logoColor=white" alt="PDF"></a> <a href="https://colab.research.google.com/github/chang-ye-tu/asm/blob/master/colab/unit10.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"></a> |
| 11/25 | **Unit 11** Decision Trees <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit11.pdf"><img src="https://img.shields.io/badge/PDF-B31B1B?logo=adobeacrobatreader&logoColor=white" alt="PDF"></a> <a href="https://colab.research.google.com/github/chang-ye-tu/asm/blob/master/colab/unit11.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"></a> |
| 12/02 | **Unit 12** Ensemble Methods <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit12.pdf"><img src="https://img.shields.io/badge/PDF-B31B1B?logo=adobeacrobatreader&logoColor=white" alt="PDF"></a> <a href="https://colab.research.google.com/github/chang-ye-tu/asm/blob/master/colab/unit12.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"></a> |
| 12/09 | **Unit 13** Unsupervised Learning <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit13.pdf"><img src="https://img.shields.io/badge/PDF-B31B1B?logo=adobeacrobatreader&logoColor=white" alt="PDF"></a> <a href="https://colab.research.google.com/github/chang-ye-tu/asm/blob/master/colab/unit13.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"></a> |
| 12/16 | **Unit 14** Convex Optimization, Support Vector Machines and Neural Networks <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit14.pdf"><img src="https://img.shields.io/badge/PDF-B31B1B?logo=adobeacrobatreader&logoColor=white" alt="PDF"></a> <a href="https://colab.research.google.com/github/chang-ye-tu/asm/blob/master/colab/unit14.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"></a> |
| **12/23** | **Final exam** |

## SRM 指定閱讀範圍對照

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

- ISLR 第 5 章 SRM 僅指定 5.1 與 5.3，**§5.2 拔靴法不在其範圍內**，本課程仍納入（bagging 需要）。
- 第 8 章排除 8.2.4（BART）與 8.2.5，但 **8.2.3 boosting 在範圍內**。
- AIC、BIC 採 ISLR §6.1.3 之定義：AIC = (RSS + 2d·σ̂²)/n，BIC = (RSS + ln(n)·d·σ̂²)/n。

## 授課教師

changytu @ o365.fcu.edu.tw
