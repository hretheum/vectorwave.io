# 🚢 Vector Wave - Port Allocation Registry

## 📊 Current Port Allocation Status

### **RESERVED PORTS** (In Use)

#### **Core Infrastructure (3000-3999)**
- **3000**: Grafana (Publisher)
- **3001**: Grafana (Kolegium) / LinkedIn Dashboard
- **3100**: Health Dashboard (Publisher Production)

#### **Database & Cache (5000-6999)**
- **5432**: PostgreSQL (Kolegium)
- **5678**: n8n Workflow Engine
- **6379**: Redis (Kolegium)
- **6380**: Redis (AI Writing Flow Minimal)
- **6381**: Redis (Publisher)

#### **API Services (8000-8099)**
- **8000**: ChromaDB (Kolegium) / LinkedIn Module
- **8001**: Kolegium API / ChromaDB (AI Writing Flow)
- **8003**: AI Writing Flow
- **8004**: Enhanced AI Writing Flow
- **8081**: Nginx Proxy (Publisher)
- **8082**: Knowledge Base
- **8083**: Twitter Adapter
- **8084**: Beehiiv Adapter - **⚠️ KONFLIKT Z PLANEM EDITORIAL SERVICE**
- **8085**: Publisher Orchestrator
- **8086**: Ghost Adapter
- **8088**: LinkedIn Adapter
- **8089**: Presenton Service
- **8090**: LinkedIn Production Service
- **8098**: LinkedIn Runner

#### **Monitoring (9000-9999)**
- **9090**: Prometheus (Publisher) / Knowledge Base Metrics
- **9091**: Prometheus (Kolegium)

---

## ⚠️ PORT CONFLICTS DETECTED

### **Critical Conflict**:
- **8084**: Currently used by **Beehiiv Adapter** (Publisher)
- **8084**: Planned for **Editorial Service** (StyleGuide Migration Plan)

**Resolution Required**: Editorial Service must use different port

---

## 🎯 PORT ALLOCATION STRATEGY

### **Port Range Assignments**

#### **3000-3999: Frontend & Dashboards**
- 3000-3099: Grafana instances
- 3100-3199: Health dashboards
- 3200-3299: **RESERVED** for future UI services
- 3300-3999: **AVAILABLE**

#### **4000-4999: Development & Testing**
- **COMPLETELY AVAILABLE** for temporary services

#### **5000-5999: Specialized Services**
- 5000-5099: Workflow engines (n8n: 5678)
- 5100-5999: **AVAILABLE**

#### **6000-6999: Data Storage**
- 6000-6099: Database ports (PostgreSQL: 5432 exception)
- 6100-6199: Cache systems (Redis: 6379-6381)
- 6200-6999: **AVAILABLE**

#### **7000-7999: Message Queues & Communication**
- **COMPLETELY AVAILABLE**

#### **8000-8099: Core API Services**
- 8000-8009: Infrastructure APIs
- 8010-8019: Content APIs  
- 8020-8029: Publishing APIs
- 8030-8039: AI Services
- 8040-8049: Editorial Services (**8084 CONFLICT**)
- 8050-8059: Integration APIs
- 8060-8069: Analytics APIs
- 8070-8079: **AVAILABLE**
- 8080-8089: Platform Adapters
- 8090-8099: Specialized Services

#### **9000-9999: Monitoring & Metrics**
- 9000-9099: Prometheus instances
- 9100-9199: Metrics exporters
- 9200-9999: **AVAILABLE**

---

## 📋 NEW SERVICE ALLOCATION RULES

### **Automatic Port Assignment Process**

1. **Check Conflict**: Always verify against this document
2. **Range Selection**: Choose appropriate range by service type
3. **Sequential Allocation**: Use next available port in chosen range
4. **Documentation**: Update this document immediately
5. **Validation**: Test port availability in all environments

### **Service Type to Port Range Mapping**

```yaml
service_types:
  frontend: 3000-3999
  development: 4000-4999
  workflow: 5000-5999
  database: 6000-6999
  messaging: 7000-7999
  api: 8000-8099
  monitoring: 9000-9999
```

### **Port Reservation Process**

1. **Identify Service Type**
2. **Find Next Available Port** in appropriate range
3. **Reserve Port** by adding to this document
4. **Update Docker Compose** files
5. **Update Service Documentation**
6. **Test Conflicts** across all environments

---

## 🔧 MIGRATION PLAN PORT UPDATES

### **Original Plan (CONFLICTED)**:
- Editorial Service: **8084** ❌ **CONFLICT** with Beehiiv Adapter

### **Revised Plan**:
- **Editorial Service**: **8040** ✅ (Editorial Services range)
- **Alternative Options**: 8041, 8042, 8043, 8044

### **Updated Migration Plan Requirements**:
- Change all references from `localhost:8084` to `localhost:8040`
- Update docker-compose.yml port mapping: `8040:8080`
- Update AI Writing Flow client configuration
- Update health check endpoints

---

## 📚 DOCUMENTATION REFERENCES

### **Files Requiring Port Documentation Updates**:

#### **Main Project Documentation**:
- `/Users/hretheum/dev/bezrobocie/vector-wave/README.md`
- `/Users/hretheum/dev/bezrobocie/vector-wave/PROJECT_CONTEXT.md`

#### **Publisher Documentation**:
- `/Users/hretheum/dev/bezrobocie/vector-wave/publisher/README.md`
- `/Users/hretheum/dev/bezrobocie/vector-wave/publisher/PROJECT_CONTEXT.md`

#### **Kolegium Documentation**:
- `/Users/hretheum/dev/bezrobocie/vector-wave/kolegium/README.md`
- `/Users/hretheum/dev/bezrobocie/vector-wave/kolegium/PROJECT_CONTEXT.md`

#### **LinkedIn Module Documentation**:
- `/Users/hretheum/dev/bezrobocie/vector-wave/linkedin/README.md`

#### **Migration Plan**:
- `/Users/hretheum/dev/bezrobocie/vector-wave/STYLEGUIDE_CHROMADB_MIGRATION_PLAN.md`

---

## 🚨 CRITICAL ACTIONS REQUIRED

### **Immediate Tasks**:

1. **Update Migration Plan**: Change Editorial Service port from 8084 to 8040
2. **Verify Beehiiv Adapter**: Confirm 8084 usage in production
3. **Update Documentation**: Add port allocation references to all project docs
4. **Create Port Check Script**: Automated conflict detection
5. **Docker Compose Updates**: Ensure all compose files reference this document

### **Port Allocation Check Commands**:

```bash
# Check current port usage
netstat -tulpn | grep LISTEN | grep -E ':(3[0-9]{3}|[4-9][0-9]{3})'

# Check Docker container ports
docker ps --format "table {{.Names}}\t{{.Ports}}"

# Verify port availability before allocation
nc -zv localhost [PORT_NUMBER]
```

---

## 📊 PORT UTILIZATION SUMMARY

- **Total Ports Allocated**: 23 ports
- **Port Range Usage**:
  - 3000-3999: 3 ports (7.5% utilized)
  - 5000-5999: 2 ports (2% utilized) 
  - 6000-6999: 3 ports (3% utilized)
  - 8000-8099: 13 ports (13% utilized)
  - 9000-9999: 2 ports (2% utilized)
- **Available Ranges**: 4000-4999 (100% available), 7000-7999 (100% available)
- **Critical Conflicts**: 1 (Editorial Service vs Beehiiv Adapter)

---

**⚠️ MANDATORY**: Before implementing any new service, consult this document and update port allocations. All services must document their port usage here.