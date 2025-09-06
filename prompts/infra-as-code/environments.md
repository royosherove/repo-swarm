version=1
Act as an infrastructure environment specialist. Analyze how this infrastructure-as-code project manages different environments and deployment strategies.

**Special Instruction**: Only document environment management strategies that are ACTUALLY implemented in the codebase. Do NOT list environment management tools, deployment strategies, or configurations that are not present.

Please analyze:

1. **Environment Identification:**
   - What environments are defined (dev, staging, prod, etc.)?
   - How are environments differentiated in the code?
   - Environment-specific configurations or overrides

2. **Variable Management:**
   - How are environment-specific variables handled?
   - Variable files structure (tfvars, values.yaml, group_vars)
   - Secret management approach per environment

3. **Resource Segregation:**
   - How are resources isolated between environments?
   - Naming conventions for environment separation
   - Network isolation strategies

4. **Deployment Strategy:**
   - Blue-green, canary, or rolling deployment configurations
   - Environment promotion process
   - Rollback mechanisms

5. **Scaling Differences:**
   - Resource sizing variations between environments
   - Cost optimization strategies for non-production
   - High availability configurations per environment

6. **Access Control:**
   - Environment-specific IAM policies
   - Service account management
   - Developer vs production access patterns

7. **Disaster Recovery:**
   - Backup strategies per environment
   - RTO/RPO configurations
   - Cross-region failover setups

Format the output clearly using markdown

---

## Repository Structure and Files

{repo_structure}

