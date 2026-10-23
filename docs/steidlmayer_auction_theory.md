# Steidlmayer Auction Theory & Market Profile Foundations

## 1. Introduction & Historical Background

**Market Profile** was developed in the early 1980s by **J. Peter Steidlmayer** at the **Chicago Board of Trade (CBOT)**. It represents a foundational framework for understanding how financial markets facilitate trade through two-way auctions.

Traditional financial charts display price along the vertical axis and chronological time along the horizontal axis. In contrast, Market Profile organizes market activity into a **distribution of price over time**, highlighting where participants perceive **fair value** versus where price was merely advertising for other timeframe buyers or sellers.

```text
       Price
         ▲
         │          A
         │        A B C
         │      A B C D E
  VAH ───┼──  A B C D E F G ───────── Upper Value Area Boundary (70%)
         │    A B C D E F G H
  POC ───┼──  A B C D E F G H I ───── Point of Control (Highest Activity)
         │    A B C D E F G H
  VAL ───┼──  A B C D E F G ───────── Lower Value Area Boundary (70%)
         │      C D E F
         │        D E
         │          E
         └─────────────────────────► TPO Count / Frequency
```

---

## 2. Core Concepts of Market Profile

### 2.1 Time-Price Opportunity (TPO)
A **TPO** is the basic atomic building block of Market Profile.
- A trading session is partitioned into standardized discrete intervals, traditionally **30 minutes**, called **brackets**.
- Each bracket is assigned an alphabetic letter: `A` (00:00 - 00:30 UTC), `B` (00:30 - 01:00 UTC), `C` (01:00 - 01:30 UTC), ..., `X` (23:30 - 24:00 UTC).
- Whenever the market touches a discrete price row during bracket $K$, that row is credited with one TPO print.

### 2.2 Initial Balance (IB)
The **Initial Balance (IB)** represents the price range established during the first hour of the session (typically brackets `A` and `B`):
$$
\text{IB High} = \max(\text{High}_A, \text{High}_B)
$$
$$
\text{IB Low} = \min(\text{Low}_A, \text{Low}_B)
$$
The Initial Balance acts as the baseline benchmark for intraday conviction:
- **Narrow IB**: Market participants are hesitant; high probability of a directional range extension (Trend Day).
- **Wide IB**: Both aggressive buyers and sellers have committed large capital early; high probability of a rotational bracketed session (Normal Day).

### 2.3 Point of Control (POC)
The **POC** is the discrete price level that accumulated the greatest number of TPO prints during the session. It represents the price of **maximum efficiency and acceptance**, where the two-way auction spent the most time facilitating trade.

### 2.4 Value Area (70% Rule)
Steidlmayer posited that market auction distributions approximate a Gaussian bell curve. In statistics, approximately 68.2% of observations fall within $\pm 1$ standard deviation of the mean.

The Market Profile **Value Area (VA)** designates the contiguous range between **Value Area Low (VAL)** and **Value Area High (VAH)** that encloses exactly **70% of the total session TPOs**, centered around the POC.

---

## 3. Structural Classifications

### 3.1 Profile Shapes
1. **'D'-shape (Balanced / Normal Auction)**:
   - Symmetrical bell-shaped profile with POC situated near the center (32% - 68% of range).
   - Indicates equilibrium between buyers and sellers with rotational trading.
2. **'P'-shape (Short-Covering / Buying Imbalance)**:
   - Thin stem at the lower extreme, fat distribution at the upper extreme (POC $\ge$ 68% of range).
   - Indicates aggressive buying conviction or trapped short sellers liquidating.
3. **'b'-shape (Long Liquidation / Selling Imbalance)**:
   - Thin stem at the upper extreme, fat distribution at the lower extreme (POC $\le$ 32% of range).
   - Indicates aggressive selling conviction or long positions dumping inventory.
4. **'B'-shape (Double Distribution Trend Day)**:
   - Two distinct high-TPO balance distributions separated by an interior single-print vacuum.
   - Represents an initiative trend day where the market abandoned the first balance area and found value higher/lower.

### 3.2 Extremes: Excess Tails vs Poor Extremes
- **Excess Tail**: A single-print tail (row count = 1 followed immediately by count $\ge 2$). Indicates rapid, decisive rejection by longer-term other-timeframe participants. Serves as strong structural support/resistance.
- **Poor Extreme (Blunt Edge)**: An extreme with $\ge 2$ TPOs. Indicates that the market stopped moving because it ran out of session time, not because opposing participants stepped in. Represents an **unfinished auction** with high probability of retesting.

### 3.3 Single Prints
Contiguous price rows inside the body of the profile having exactly 1 TPO. Single prints mark zones where price moved so rapidly that very little trade facilitation occurred. In future sessions, single prints act as vacuum zones or strong support/resistance boundaries.

---

## 4. Academic & Industry Literature

1. **Steidlmayer, J. P., & Hawkins, K. (1986)**. *Markets & Market Logic: A New Way to Recognize and Profit from Market Shifts*. Porcupine Press.
2. **Chicago Board of Trade (CBOT) (1991)**. *CBOT Market Profile: A Flexible, Dynamic Approach to Market Analysis*.
3. **Dalton, J. F., Jones, E. T., & Dalton, R. B. (1999)**. *Mind Over Markets: Power Trading with Market Generated Information*. John Wiley & Sons.
