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
| 09/09 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit01.pdf">**Unit 1** Statistical Learning</a> <a href="https://colab.research.google.com/github/chang-ye-tu/asm/blob/master/colab/unit01.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"></a><br>1.1 What statistical learning is: the regression function, reducible and irreducible error; parametric and non-parametric methods; summary statistics, power transforms, sampling and study design<br>1.2 Assessing model accuracy: training and test error, the bias–variance decomposition, the Bayes classifier and KNN<br>1.3 Resampling: the validation set approach, LOOCV and its shortcut, *k*-fold CV; the bootstrap (beyond the syllabus) |
| 09/16 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit02.pdf">**Unit 2** Multiple Regression I: Matrix Theory</a> <a href="https://colab.research.google.com/github/chang-ye-tu/asm/blob/master/colab/unit02.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"></a><br>2.1 Normal equations, the hat matrix, orthogonal projection, leverage<br>2.2 Unbiasedness, var(**b**), the Gauss–Markov theorem, estimation of σ²<br>2.3 Exact inference under normality; goodness of fit; **the case *k*=1**: *r*, *R*²=*r*², CAPM |
| 09/23 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit03.pdf">**Unit 3** Multiple Regression II: Inference and Interpretation</a> <a href="https://colab.research.google.com/github/chang-ye-tu/asm/blob/master/colab/unit03.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"></a><br>3.1 Inference for one coefficient: tests and intervals; added variable plots, partial correlation and the FWL theorem<br>3.2 Several coefficients: restricted least squares, the general linear hypothesis, extra sums of squares; qualitative, transformed and interaction variables<br>3.3 Interpreting regression results: significance and causation, omitted and extraneous variables; the marketing plan |
| 09/30 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit04.pdf">**Unit 4** Regression Diagnostics</a> <a href="https://colab.research.google.com/github/chang-ye-tu/asm/blob/master/colab/unit04.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"></a><br>4.1 The iterative approach; residual analysis: standardised and studentised residuals, outliers, residuals against other variables, correlated errors<br>4.2 Influential points: leverage as a distance, Cook's distance, DFFITS/DFBETAS; collinearity: VIF, suppressor and orthogonal variables<br>4.3 Heteroscedasticity: the Breusch–Pagan test, robust standard errors, weighted least squares, transformations |
| 10/07 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit05.pdf">**Unit 5** Variable Selection and Dimension Reduction</a> <a href="https://colab.research.google.com/github/chang-ye-tu/asm/blob/master/colab/unit05.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"></a><br>5.1 Subset selection: best subset, forward, backward and stepwise selection, RSS steps as *t* steps, data snooping; selection criteria: the optimism of the training error, *C*<sub>p</sub>, AIC, BIC, adjusted *R*², the likelihood ratio test, validation, cross-validation, PRESS and the one-standard-error rule<br>5.2 Principal components: eigenvectors, proportion of variance explained, the best low-rank approximation; principal components regression (PCR) and partial least squares (PLS)<br>5.3 Data collection: sampling frames, selection on the predictors, truncation and censoring, extrapolation, omitted variables and missing data; the ISLR labs |
| 10/14 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit06.pdf">**Unit 6** Shrinkage, Nearest Neighbours and High Dimensions</a> <a href="https://colab.research.google.com/github/chang-ye-tu/asm/blob/master/colab/unit06.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"></a><br>6.1 Ridge regression: closed form for any rank, shrinkage along the principal components, the Hoerl–Kennard risk, effective degrees of freedom<br>6.2 The lasso: the constrained form, stationarity and sparsity, soft thresholding, the Bayesian view; coordinate descent and the elastic net<br>6.3 Choosing λ by cross-validation; the exact ridge LOOCV shortcut<br>6.4 KNN regression against least squares; the curse of dimensionality<br>6.5 High dimensions: perfect fits, failing criteria, regularised fits<br>6.6 The ISLR lab (ridge and lasso); formulas against glmnet |
| 10/21 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit07.pdf">**Unit 7** Generalized Linear Models I: Categorical Responses</a> <a href="https://colab.research.google.com/github/chang-ye-tu/asm/blob/master/colab/unit07.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"></a><br>7.1 Binary responses: classification against regression, coding a qualitative response, the linear probability model and its three drawbacks<br>7.2 Logistic and probit regression: threshold and random-utility interpretations, odds ratios, logit against probit<br>7.3 Likelihood inference: score and information, concavity, existence and separation, large-sample theory, Wald and likelihood ratio tests, measures of fit; ISLR's `Default` data and confounding<br>7.4 FREES's MEPS application (Tables 11.4–11.5 reproduced)<br>7.5 Nominal responses: generalized, multinomial and nested logits<br>7.6 Ordinal responses: cumulative logit and probit<br>7.7 Classification by threshold (ROC and AUC beyond the syllabus); 7.8 Computation in R and the ISLR lab |
| 10/28 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit08.pdf">**Unit 8** Generalized Linear Models II: Counts and the Exponential Family</a> <a href="https://colab.research.google.com/github/chang-ye-tu/asm/blob/master/colab/unit08.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"></a><br>8.1 Counts: the Poisson distribution, Pearson's goodness-of-fit statistic, linear regression on counts<br>8.2 Poisson regression: exposure and offsets, estimation and existence, large-sample inference, Pearson residuals<br>8.3 FREES's Singapore automobile application (Tables 12.4–12.7 reproduced)<br>8.4 Overdispersion: quasi-Poisson, robust standard errors, the negative binomial<br>8.5 Zero-inflated, hurdle, heterogeneity and latent class models<br>8.6 Generalized linear models: the linear exponential family, links, estimation and IRLS, deviance<br>8.7 FREES's medical expenditure application: gamma and inverse Gaussian regression (Table 13.6 reproduced)<br>8.8 Residuals; 8.9 the Tweedie distribution; 8.10 the ISLR lab and computation in R |
| **11/04** | **Midterm exam** |
| 11/11 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit09.pdf">**Unit 9** Modeling Trends</a> <a href="https://colab.research.google.com/github/chang-ye-tu/asm/blob/master/colab/unit09.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"></a><br>9.1 Time series and trends: spurious regression, polynomial trends and their leverage, seasonal indicators<br>9.2 Stationarity, white noise and the random walk; exact forecast intervals<br>9.3 Inference with random walks: forecasting, control charts, identifying a random walk, random walk against linear trend<br>9.4 Filtering: transformations and differences of logarithms<br>9.5 Forecast evaluation out of sample<br>9.6 Autocorrelations and the Durbin–Watson statistic; 9.7 computation in R |
| 11/18 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit10.pdf">**Unit 10** Autoregressive Models and Forecasting</a> <a href="https://colab.research.google.com/github/chang-ye-tu/asm/blob/master/colab/unit10.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"></a><br>10.1 The AR(1) model: existence, moments, the correlogram and its band<br>10.2 Conditional least squares and its large-sample theory; residual checking<br>10.3 Smoothing and prediction: the chain rule and forecast intervals<br>10.4 Box–Jenkins ARIMA models and an autoregression for NYSE volume (beyond the syllabus)<br>10.5 Moving averages, exponential and double exponential smoothing, Holt's method<br>10.6 Seasonal models: trigonometric terms, seasonal autoregression, Holt–Winters<br>10.7 Unit root tests; 10.8 ARCH/GARCH<br>10.9 Regression trees: recursive binary splitting; 10.10 computation in R |
| 11/25 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit11.pdf">**Unit 11** Decision Trees</a> <a href="https://colab.research.google.com/github/chang-ye-tu/asm/blob/master/colab/unit11.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"></a><br>11.1 Cost-complexity pruning: the pruning family, nested minimising subtrees, choosing α by cross-validation<br>11.2 Classification trees: leaf labels, the Gini index, entropy and the misclassification rate, two classes, categorical predictors<br>11.3 Trees against linear models: the cost of a staircase, where a tree is exactly right, instability<br>11.4 Computation in R: the ISLR labs (`Carseats`, `Boston`), growing, pruning and selecting in practice |
| 12/02 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit12.pdf">**Unit 12** Ensemble Methods</a> <a href="https://colab.research.google.com/github/chang-ye-tu/asm/blob/master/colab/unit12.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"></a><br>12.1 Bagging: averaging correlated predictors, the bootstrap ensemble, majority vote, out-of-bag estimation, variable importance<br>12.2 Random forests: decorrelation, what it costs; ISLR's `Heart` example<br>12.3 Boosting: fitting the residuals, boosting a linear learner, shrinkage against rounds, depth and interaction; the hyperparameters<br>12.4 Computation in R: the ISLR labs on `Boston`, formulas against package output, ensembles in practice |
| 12/09 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit13.pdf">**Unit 13** Unsupervised Learning</a> <a href="https://colab.research.google.com/github/chang-ye-tu/asm/blob/master/colab/unit13.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"></a><br>13.1 Unsupervised learning; principal components recalled, the biplot<br>13.2 *K*-means clustering: the criterion, Lloyd's algorithm, local optima<br>13.3 Hierarchical clustering: linkages, dendrograms, inversions, single-linkage chains, correlation-based distance<br>13.4 Practical issues: choosing *K*, standardisation, validation, robustness<br>13.5 Computation in R: the ISLR labs (simulated data, `NCI60`), clustering in practice |
| 12/16 | <a href="https://github.com/chang-ye-tu/asm/blob/master/note/unit14.pdf">**Unit 14** Convex Optimization, Support Vector Machines and Neural Networks</a> <a href="https://colab.research.google.com/github/chang-ye-tu/asm/blob/master/colab/unit14.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"></a><br>14.1 Convex optimisation: convex problems, local and global minima, the dual of a quadratic programme, gradient descent and Newton's method<br>14.2 Support vector classifiers: the maximal margin classifier, the dual and support vectors, the soft margin and the hinge loss<br>14.3 Support vector machines: kernels, more than two classes, relation to logistic regression<br>14.4 Neural networks: the multilayer perceptron, backpropagation, ReLU networks, non-convexity and SGD, softmax and convolution, recurrent networks<br>14.5 Computation in R: the ISLR labs (SVM, `Khan`, `Hitters` and `NYSE` networks in torch); exercises from ISLR and from Boyd and Vandenberghe's *Convex Optimization* |
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
