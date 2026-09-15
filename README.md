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
| 09/09 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit01.pdf">**Unit 1** Statistical Learning</a><br>1.1 What statistical learning is: the regression function, reducible and irreducible error; parametric and non-parametric methods; summary statistics, power transforms, sampling and study design<br>1.2 Assessing model accuracy: training and test error, the bias–variance decomposition, the Bayes classifier and KNN<br>1.3 Resampling: the validation set approach, LOOCV and its shortcut, *k*-fold CV; the bootstrap (beyond the syllabus) |
| 09/16 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit02.pdf">**Unit 2** Multiple Regression I: Matrix Theory</a><br>2.1 Normal equations, the hat matrix, orthogonal projection, leverage<br>2.2 Unbiasedness, var(**b**), the Gauss–Markov theorem, estimation of σ²<br>2.3 Exact inference under normality; goodness of fit; **the case *k*=1**: *r*, *R*²=*r*², CAPM |
| 09/23 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit03.pdf">**Unit 3** Multiple Regression II: Inference and Interpretation</a><br>3.1 Inference on one and several coefficients: *t*, the general linear hypothesis, extra sum of squares<br>3.2 Confidence and prediction intervals; special explanatory variables: binary, categorical, interactions<br>3.3 The FWL theorem, omitted-variable bias, interpreting regression output |
| 09/30 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit04.pdf">**Unit 4** Regression Diagnostics</a><br>4.1 Iterative modelling; residual analysis, standardised and studentised residuals<br>4.2 Influential points: leverage, Cook's D, DFFITS/DFBETAS<br>4.3 Collinearity and VIF; heteroscedasticity, robust standard errors and weighted least squares |
| 10/07 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit05.pdf">**Unit 5** Variable Selection and Dimension Reduction</a><br>5.1 Best subset, forward, backward and stepwise selection<br>5.2 Selection criteria: *C*<sub>p</sub>, AIC, BIC, adjusted *R*², the likelihood ratio test<br>5.3 Principal components; principal components regression (PCR) and partial least squares (PLS) |
| 10/14 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit06.pdf">**Unit 6** Shrinkage, High Dimensions and KNN</a><br>6.1 Ridge regression: closed form, shrinkage along principal components, effective degrees of freedom<br>6.2 The lasso and the elastic net; choosing λ by CV<br>6.3 Regression in high dimensions; KNN against OLS; linear models in R |
| 10/21 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit07.pdf">**Unit 7** Generalized Linear Models I: Categorical Responses</a><br>7.1 Binary responses: the linear probability model, logistic and probit regression, odds ratios<br>7.2 Likelihood inference: MLE, Wald and likelihood ratio tests; classification metrics and ROC<br>7.3 Nominal responses (generalized logit); ordinal responses (cumulative logit) |
| 10/28 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit08.pdf">**Unit 8** Generalized Linear Models II: Counts and the Exponential Family</a><br>8.1 Poisson regression, exposure and offsets<br>8.2 Overdispersion; negative binomial, zero-inflated and hurdle models<br>8.3 The linear exponential family and link functions; IRLS, deviance residuals, the Tweedie distribution |
| **11/04** | **Midterm exam** |
| 11/11 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit09.pdf">**Unit 9** Modeling Trends</a><br>9.1 Fitting time trends; seasonal effects by regression<br>9.2 Stationarity and random walks; inference under a random walk; differencing<br>9.3 Evaluating forecasts; autocorrelations |
| 11/18 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit10.pdf">**Unit 10** Autoregressive Models and Forecasting</a><br>10.1 AR(1), AR(p), MA(q) and ARIMA; partial autocorrelations; large-sample properties of conditional least squares, residual diagnostics and Ljung–Box, forecasting<br>10.2 Moving averages and exponential smoothing; seasonal models; unit-root tests; ARCH/GARCH<br>10.3 Introduction to decision trees: recursive binary splitting, regression trees |
| 11/25 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit11.pdf">**Unit 11** Decision Trees</a><br>11.1 Cost-complexity pruning; choosing α by CV<br>11.2 Classification trees: the Gini index, entropy, the misclassification rate<br>11.3 Trees against linear models; trees in R |
| 12/02 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit12.pdf">**Unit 12** Ensemble Methods</a><br>12.1 Bagging and out-of-bag error; variable importance<br>12.2 Random forests: decorrelation and mtry<br>12.3 Boosting; ensembles in R |
| 12/09 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit13.pdf">**Unit 13** Unsupervised Learning</a><br>13.1 Principal components analysis: loadings, scores, proportion of variance explained, scree plots<br>13.2 *K*-means clustering<br>13.3 Hierarchical clustering: dendrograms, linkages; unsupervised learning in R |
| 12/16 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit14.pdf">**Unit 14** Convex Optimization, Support Vector Machines and Neural Networks</a><br>14.1 Lagrangian duality and the KKT conditions; the maximal margin classifier<br>14.2 The dual SVM and support vectors; soft margins and kernels<br>14.3 Multilayer perceptrons and backpropagation; R implementation |
| **12/23** | **Final exam** |

## SRM 指定閱讀範圍對照

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

- ISLR 第 5 章 SRM 僅指定 5.1 與 5.3，**§5.2 拔靴法不在其範圍內**，本課程仍納入（bagging 需要）。
- 第 8 章排除 8.2.4（BART）與 8.2.5，但 **8.2.3 boosting 在範圍內**。
- AIC、BIC 採 ISLR §6.1.3 之定義：AIC = (RSS + 2d·σ̂²)/n，BIC = (RSS + ln(n)·d·σ̂²)/n。

## 授課教師

changytu @ o365.fcu.edu.tw
