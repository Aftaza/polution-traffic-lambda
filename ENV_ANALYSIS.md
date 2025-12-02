# Environment Variables Analysis & Fix

## 🔍 **Analisis Masalah**

### **Issue Ditemukan:** ❌ API Keys Tidak Dicantumkan di Docker Compose

#### **1. Yang Ada di `.env.example`:**
```env
# API Keys (replace with your actual API keys)
TOMTOM_API_KEY=your_tomtom_api_key_here
AQICN_TOKEN=your_aqicn_token_here
```

#### **2. Yang Ada di `docker-compose.yml` (ingestion_service):**
```yaml
ingestion_service:
  env_file:
    - .env
  environment:
    POSTGRES_HOST: db
    POSTGRES_DB: ${POSTGRES_DB:-pid_db}
    POSTGRES_USER: ${POSTGRES_USER:-pid_user}
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-pid_password}
    KAFKA_BOOTSTRAP_SERVERS: kafka:9092
    KAFKA_TOPIC: traffic-aqi-data
    # ❌ MISSING: TOMTOM_API_KEY
    # ❌ MISSING: AQICN_TOKEN
```

#### **3. Yang Dibutuhkan oleh Code (`utils.py`):**
```python
def validate_api_keys():
    """Validate that required API keys are present."""
    tomtom_api_key = os.getenv("TOMTOM_API_KEY")  # ✅ Required
    aqicn_token = os.getenv("AQICN_TOKEN")        # ✅ Required
    
    if not tomtom_api_key or not aqicn_token:
        raise ValueError("TOMTOM_API_KEY and AQICN_TOKEN must be set")
```

---

## ⚠️ **Mengapa Ini Masalah?**

### **Scenario 1: env_file Alone**
```yaml
ingestion_service:
  env_file:
    - .env  # ✅ Loads TOMTOM_API_KEY and AQICN_TOKEN
```
**Problem:** 
- ❌ Variables dari `env_file` bisa di-override oleh `environment` section
- ❌ Tidak ada fallback values
- ❌ Tidak eksplisit, sulit di-debug

### **Scenario 2: environment Section Alone**
```yaml
ingestion_service:
  environment:
    POSTGRES_HOST: db
    # ❌ API keys tidak ada
```
**Problem:**
- ❌ API keys tidak ter-pass ke container
- ❌ Ingestion service akan crash dengan error

### **Current State:**
```yaml
ingestion_service:
  env_file:
    - .env              # Loads all vars from .env
  environment:
    POSTGRES_HOST: db   # Overrides specific vars
    # API keys dari .env SHOULD work, tapi tidak eksplisit
```

**Status:** ⚠️ **Technically works, but NOT EXPLICIT and RISKY**

---

## ✅ **Solusi: Explicit Environment Variables**

### **Best Practice:**

1. **Declare ALL required variables explicitly**
2. **Use ${VAR:-default} syntax for fallbacks**
3. **Keep env_file for convenience**
4. **Override in environment section for clarity**

### **Fixed docker-compose.yml:**

```yaml
# 4. Ingestion Service - Kafka Producer (API Polling)
ingestion_service:
  build: .
  container_name: pid-ingestion-producer
  restart: always
  command: python ingestion_service.py
  env_file:
    - .env
  environment:
    # Database Configuration
    POSTGRES_HOST: db
    POSTGRES_DB: ${POSTGRES_DB:-pid_db}
    POSTGRES_USER: ${POSTGRES_USER:-pid_user}
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-pid_password}
    
    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: kafka:9092
    KAFKA_TOPIC: traffic-aqi-data
    
    # API Keys - EXPLICITLY DECLARED ✅
    TOMTOM_API_KEY: ${TOMTOM_API_KEY}
    AQICN_TOKEN: ${AQICN_TOKEN}
  depends_on:
    kafka:
      condition: service_healthy
    db:
      condition: service_healthy
  networks:
    - pid_network
```

---

## 📊 **Comparison: Before vs After**

### **Before (Current):**
```yaml
environment:
  POSTGRES_HOST: db
  POSTGRES_DB: ${POSTGRES_DB:-pid_db}
  KAFKA_BOOTSTRAP_SERVERS: kafka:9092
  # ❌ API keys implicit (dari env_file)
```

**Issues:**
- ❌ Not clear that API keys are required
- ❌ Hard to debug if .env is missing
- ❌ No validation at docker-compose level
- ❌ Inconsistent with other variables

### **After (Fixed):**
```yaml
environment:
  POSTGRES_HOST: db
  POSTGRES_DB: ${POSTGRES_DB:-pid_db}
  KAFKA_BOOTSTRAP_SERVERS: kafka:9092
  TOMTOM_API_KEY: ${TOMTOM_API_KEY}      # ✅ Explicit
  AQICN_TOKEN: ${AQICN_TOKEN}            # ✅ Explicit
```

**Benefits:**
- ✅ Clear documentation of required variables
- ✅ Easy to debug (docker-compose config shows all vars)
- ✅ Fails fast if .env is missing
- ✅ Consistent with other environment variables

---

## 🔧 **Complete Environment Variables Mapping**

### **Services that Need API Keys:**

| Service | TOMTOM_API_KEY | AQICN_TOKEN | Reason |
|---------|----------------|-------------|--------|
| **ingestion_service** | ✅ YES | ✅ YES | Polls external APIs |
| speed_layer | ❌ NO | ❌ NO | Only processes Kafka messages |
| batch_layer | ❌ NO | ❌ NO | Only processes database data |
| streamlit_app | ❌ NO | ❌ NO | Only displays data |

### **All Environment Variables by Service:**

#### **ingestion_service:**
```yaml
POSTGRES_HOST: db
POSTGRES_DB: ${POSTGRES_DB:-pid_db}
POSTGRES_USER: ${POSTGRES_USER:-pid_user}
POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-pid_password}
KAFKA_BOOTSTRAP_SERVERS: kafka:9092
KAFKA_TOPIC: traffic-aqi-data
TOMTOM_API_KEY: ${TOMTOM_API_KEY}      # ✅ ADDED
AQICN_TOKEN: ${AQICN_TOKEN}            # ✅ ADDED
```

#### **speed_layer:**
```yaml
POSTGRES_HOST: db
POSTGRES_DB: ${POSTGRES_DB:-pid_db}
POSTGRES_USER: ${POSTGRES_USER:-pid_user}
POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-pid_password}
KAFKA_BOOTSTRAP_SERVERS: kafka:9092
KAFKA_TOPIC: traffic-aqi-data
KAFKA_CONSUMER_GROUP: speed-layer-consumer
# No API keys needed ✅
```

#### **batch_layer:**
```yaml
POSTGRES_HOST: db
POSTGRES_DB: ${POSTGRES_DB:-pid_db}
POSTGRES_USER: ${POSTGRES_USER:-pid_user}
POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-pid_password}
# No API keys needed ✅
```

#### **streamlit_app:**
```yaml
POSTGRES_HOST: db
POSTGRES_DB: ${POSTGRES_DB:-pid_db}
POSTGRES_USER: ${POSTGRES_USER:-pid_user}
POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-pid_password}
# No API keys needed ✅
```

---

## ✅ **Verification Checklist**

### **1. .env File:**
```bash
# Check if .env exists and has API keys
cat .env | grep -E "TOMTOM_API_KEY|AQICN_TOKEN"
```

Expected output:
```
TOMTOM_API_KEY=actual_key_here
AQICN_TOKEN=actual_token_here
```

### **2. Docker Compose Config:**
```bash
# Verify environment variables are loaded
docker-compose config | grep -A 20 ingestion_service
```

Should show:
```yaml
TOMTOM_API_KEY: actual_key_here
AQICN_TOKEN: actual_token_here
```

### **3. Container Environment:**
```bash
# Check environment inside running container
docker exec pid-ingestion-producer env | grep -E "TOMTOM|AQICN"
```

Should show:
```
TOMTOM_API_KEY=actual_key_here
AQICN_TOKEN=actual_token_here
```

---

## 🎯 **Recommendation**

### **Priority: HIGH** 🔴

**Action Required:**
1. ✅ Update `docker-compose.yml` to explicitly declare API keys
2. ✅ Ensure `.env` file exists with actual API keys
3. ✅ Test with `docker-compose config` before deploying
4. ✅ Verify container can access API keys after restart

### **Why This Matters:**

1. **Prevents Silent Failures:**
   - Without explicit declaration, missing API keys might not be caught until runtime
   - Ingestion service will crash with unclear error

2. **Improves Documentation:**
   - Clear what environment variables each service needs
   - Easier for new developers to understand requirements

3. **Follows Best Practices:**
   - Explicit is better than implicit
   - Consistent with how other variables are declared
   - Easier to debug and maintain

---

## 📝 **Summary**

### **Current State:**
- ⚠️ API keys loaded via `env_file` only
- ⚠️ Not explicitly declared in `environment` section
- ⚠️ Works but risky and not clear

### **Required Fix:**
- ✅ Add `TOMTOM_API_KEY: ${TOMTOM_API_KEY}` to ingestion_service
- ✅ Add `AQICN_TOKEN: ${AQICN_TOKEN}` to ingestion_service
- ✅ Keep `env_file: - .env` for convenience
- ✅ Maintain consistency with other variables

### **Impact:**
- **Risk:** Medium (service might fail if .env is misconfigured)
- **Effort:** Low (2 lines to add)
- **Benefit:** High (clarity, debuggability, best practice)

---

**Status:** ⚠️ **Needs Fix**  
**Priority:** 🔴 **HIGH**  
**Effort:** ⚡ **5 minutes**
