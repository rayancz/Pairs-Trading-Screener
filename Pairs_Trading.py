import numpy as np
import statsmodels.api as sm
from statsmodels.tsa.stattools import coint
import datetime
import yfinance as yf
import matplotlib.pyplot as plt
import seaborn as sns


def find_cointegrated_pairs(data):
    n = data.shape[1]
    score_matrix = np.zeros((n, n))
    pvalue_matrix = np.ones((n, n))
    keys = data.keys()
    pairs = []

    for i in range(n):
        for j in range(i + 1, n):
            S1 = data[keys[i]]
            S2 = data[keys[j]]

            result = coint(S1, S2)
            score = result[0]
            pvalue = result[1]

            score_matrix[i, j] = score
            pvalue_matrix[i, j] = pvalue

            if pvalue < 0.05:
                pairs.append((keys[i], keys[j], pvalue))

    return score_matrix, pvalue_matrix, pairs


# Specify dates and tickers
start = datetime.datetime(2024, 6, 1)
end = datetime.datetime(2026, 6, 1)

tickers = [
    'NP3.ST', 'FABG.ST', 'DIOS.ST', 'BALD-B.ST', 'WALL-B.ST',
    'NYF.ST', 'PNDX-B.ST', 'SHOT.ST', 'CAST.ST', 'FPAR-A.ST',
    'ATRLJ-B.ST', 'CATE.ST', 'SBB-B.ST', 'CORE-B.ST',
]


# Download adjusted closing prices
df = yf.download(
    tickers,
    start=start,
    end=end,
    auto_adjust=True
)['Close']


# Forward fill missing values, then remove remaining missing rows
df.ffill(inplace=True)
df.dropna(inplace=True)


# Run cointegration test
scores, pvalues, pairs = find_cointegrated_pairs(df)


# Sort pairs by lowest p-value first
pairs.sort(key=lambda x: x[2])


# Print only statistically significant pairs
print("\nCointegrated pairs with p-value below 0.05:")
if len(pairs) == 0:
    print("No cointegrated pairs found.")
else:
    for stock1, stock2, pvalue in pairs:
        print(f"{stock1:12} - {stock2:12} | p-value = {pvalue:.4f}")


# Analyze strongest cointegrated pair
if len(pairs) > 0:
    stock1, stock2, pvalue = pairs[0]

    print("\nStrongest cointegrated pair analysis:")
    print(f"Pair: {stock1} - {stock2}")
    print(f"Cointegration p-value: {pvalue:.4f}")

    # Estimate beta / hedge ratio
    X = sm.add_constant(df[stock2])
    model = sm.OLS(df[stock1], X).fit()
    beta = model.params[stock2]

    # Calculate spread
    spread = df[stock1] - beta * df[stock2]

    # Calculate z-score
    zscore = (spread - spread.mean()) / spread.std()
    current_zscore = zscore.iloc[-1]

    # Historical z-score extremes
    max_zscore = zscore.max()
    min_zscore = zscore.min()

    print(f"Beta / hedge ratio: {beta:.4f}")
    print(f"Current spread: {spread.iloc[-1]:.4f}")
    print(f"Current z-score: {current_zscore:.2f}")
    print(f"Maximum z-score observed: {max_zscore:.2f}")
    print(f"Minimum z-score observed: {min_zscore:.2f}")

    # Simple signal logic
    if current_zscore > 2:
        print(f"Potential signal: SHORT {stock1}, LONG {stock2}")
    elif current_zscore < -2:
        print(f"Potential signal: LONG {stock1}, SHORT {stock2}")
    else:
        print("\nNo signal: spread is not unusually far from normal.\n")

    # Plot z-score
    plt.figure(figsize=(12, 5))

    plt.plot(zscore, label="Z-Score")
    plt.axhline(2, color='red', linestyle='--', label='+2')
    plt.axhline(-2, color='green', linestyle='--', label='-2')
    plt.axhline(0, color='black', linestyle='--', label='Mean')

    plt.title(f"Z-Score of Spread: {stock1} vs {stock2}")
    plt.xlabel("Date")
    plt.ylabel("Z-Score")
    plt.legend()
    plt.tight_layout()
    plt.show()


'''
#Plot heatmap showing cointegration p-values between all stock pairs
fig, ax = plt.subplots(figsize=(12, 10))

sns.heatmap(
    pvalues,
    xticklabels=df.columns,
    yticklabels=df.columns,
    cmap='RdYlGn_r',
    mask=(pvalues >= 0.10),
    annot=True,
    fmt=".3f",
    linewidths=0.5,
    cbar_kws={'label': 'Cointegration p-value'}
)

plt.title("Cointegration Test P-Values Between Stock Pairs")
plt.xlabel("Stock")
plt.ylabel("Stock")
plt.tight_layout()
plt.show()'''