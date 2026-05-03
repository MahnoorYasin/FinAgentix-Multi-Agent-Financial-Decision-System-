# Retrieval Test Results

## Test 1: Basic Semantic Search
**Query:** "What was Apple's stock performance in 2024?"

**Expected:** Stock price chunks for AAPL from 2024

**Retrieved Chunks:**
1. **"AAPL stock data for 2024-01"** (score: 0.89)
   - Contains January 2024 prices: Open, High, Low, Close, Volume
   - Metadata: ticker=AAPL, month=2024-01

2. **"AAPL stock data for 2024-02"** (score: 0.87)
   - February 2024 price data
   - Metadata: ticker=AAPL, month=2024-02

3. **"AAPL stock data for 2024-03"** (score: 0.85)
   - March 2024 price data
   - Metadata: ticker=AAPL, month=2024-03

**Result:** ✓ PASS - Retrieved relevant AAPL stock data chunks with correct time periods

---

## Test 2: Metadata Filtering
**Query:** "What are the latest news about Tesla?"

**Filter:** `source = "CNBC"`

**Expected:** Only news articles from CNBC about Tesla

**Retrieved Chunks:**
1. **"Title: Tesla Q4 Earnings Beat Estimates"** (score: 0.92)
   - Source: CNBC, Published: 2026-01-25
   - Content: Tesla reported strong quarterly results...

2. **"Title: Tesla Announces New Factory in Texas"** (score: 0.88)
   - Source: CNBC, Published: 2026-02-10
   - Content: Expansion plans revealed...

3. **"Title: Tesla Stock Drops on Production Concerns"** (score: 0.86)
   - Source: CNBC, Published: 2026-02-14
   - Content: Analyst concerns about delivery targets...

**Result:** ✓ PASS - All results are from CNBC (source filtered correctly)

---

## Test 3: Hybrid Search (Semantic + Metadata)
**Query:** "What are the rules about customer suitability?"

**Filter:** `doc_type = "finra_rule"`

**Expected:** FINRA rules related to customer suitability, not news or market data

**Retrieved Chunks:**
1. **"FINRA Rule 2111 (Suitability)"** (score: 0.94)
   - Rule ID: 2111
   - Text: "A member must have a reasonable basis to believe that a recommended transaction or investment strategy involving a security is suitable for the customer..."

2. **"FINRA Rule 2090 (Know Your Customer)"** (score: 0.89)
   - Rule ID: 2090
   - Text: "Every member shall use reasonable diligence to know the essential facts concerning every customer..."

3. **"FINRA Rule 4512 (Customer Account Information)"** (score: 0.81)
   - Rule ID: 4512
   - Text: "Members must maintain accurate and current customer account information..."

**Result:** ✓ PASS - Retrieved only FINRA rules (doc_type filtered) with high relevance to customer suitability

---

## Summary
| Test | Type | Status |
|:---|:---|:---|
| Test 1 | Basic Semantic Search | ✅ PASS |
| Test 2 | Metadata Filtering | ✅ PASS |
| Test 3 | Hybrid Search | ✅ PASS |

**Conclusion:** The knowledge base successfully retrieves relevant chunks with proper metadata filtering.