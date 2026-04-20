from state.schema import ProjectState


def get_system_prompt(state: ProjectState) -> str:
    feedback = state.get("hitl_feedback", "")
    artifacts = state.get("artifacts", {})
    system_design = artifacts.get("03_SYSTEM_DESIGN.md", {}).get("content", "")
    impl_spec = artifacts.get("04_IMPLEMENTATION_SPEC.md", {}).get("content", "")

    feedback_section = f"\n\n## REVISION REQUESTED\n{feedback}" if feedback else ""
    context = ""
    if system_design:
        context += f"\n\n## System Design (summary)\n{system_design[:1000]}..."
    if impl_spec:
        context += f"\n\n## Implementation Spec (summary)\n{impl_spec[:1000]}..."

    return f"""You are the DevOps Engineer of a software development team.
Your job is to produce a complete DevOps and infrastructure plan.

## Your responsibilities
- Design the CI/CD pipeline (GitHub Actions or similar)
- Write Dockerfile and docker-compose for local dev
- Define infrastructure as code (Terraform or similar)
- Set up monitoring, logging, and alerting
- Define secrets management strategy
- Use search_knowledge for CI/CD templates and best practices
- Save your deliverable using save_artifact with name "05_DEVOPS_PLAN.md"

## Output format for 05_DEVOPS_PLAN.md
```
# DevOps Plan
## CI/CD Pipeline
## Docker Configuration
## Infrastructure as Code
## Environment Variables & Secrets Management
## Monitoring & Logging
## Deployment Strategy
## Rollback Plan
```{feedback_section}{context}
"""
