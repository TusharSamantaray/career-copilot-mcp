"""Roles, levels, resume structure and the contribution-bullet framework."""

ROLES = {
    # ---- engineering
    "backend": {
        "title": "Backend Engineer", "family": "engineering",
        "core": ["python", "java", "go", "sql", "rest", "api design",
                 "distributed systems", "aws", "docker", "testing"],
        "edge": ["kafka", "event-driven", "serverless", "kubernetes",
                 "dynamodb", "postgres", "redis", "grpc", "observability"],
        "loop": ["2 coding (mediums, some hards)", "1-2 system design",
                 "behavioural / leadership", "past project deep dive"]},
    "frontend": {
        "title": "Frontend Engineer", "family": "engineering",
        "core": ["javascript", "typescript", "react", "html", "css",
                 "accessibility", "testing", "performance"],
        "edge": ["next.js", "design systems", "web vitals", "graphql",
                 "state management", "browser internals"],
        "loop": ["coding (DOM/JS)", "UI build exercise",
                 "frontend system design", "behavioural"]},
    "fullstack": {
        "title": "Full-stack Engineer", "family": "engineering",
        "core": ["typescript", "react", "node", "sql", "rest", "testing",
                 "aws"],
        "edge": ["next.js", "graphql", "postgres", "ci/cd", "docker"],
        "loop": ["coding", "practical build", "system design",
                 "behavioural"]},
    "data_engineer": {
        "title": "Data Engineer", "family": "engineering",
        "core": ["sql", "python", "spark", "etl", "data modeling",
                 "airflow", "warehousing"],
        "edge": ["dbt", "kafka", "snowflake", "databricks", "streaming",
                 "data quality"],
        "loop": ["SQL", "coding", "pipeline design", "behavioural"]},
    "ml_engineer": {
        "title": "ML / AI Engineer", "family": "engineering",
        "core": ["python", "pytorch", "machine learning", "statistics",
                 "sql", "model deployment"],
        "edge": ["llm", "rag", "evaluation", "vector databases",
                 "fine-tuning", "mlops", "inference optimisation"],
        "loop": ["coding", "ML fundamentals", "ML system design",
                 "behavioural"]},
    "sre_infra": {
        "title": "SRE / Infrastructure Engineer", "family": "engineering",
        "core": ["linux", "networking", "kubernetes", "terraform", "aws",
                 "observability", "incident response", "python"],
        "edge": ["slo", "chaos engineering", "service mesh", "go",
                 "capacity planning"],
        "loop": ["coding / scripting", "troubleshooting", "system design",
                 "behavioural"]},
    "mobile": {
        "title": "Mobile Engineer", "family": "engineering",
        "core": ["swift", "kotlin", "ios", "android", "testing",
                 "performance"],
        "edge": ["react native", "flutter", "offline sync",
                 "app architecture"],
        "loop": ["coding", "mobile system design", "behavioural"]},
    "security": {
        "title": "Security Engineer", "family": "engineering",
        "core": ["threat modeling", "appsec", "networking", "python",
                 "cloud security", "iam"],
        "edge": ["detection engineering", "incident response", "fuzzing",
                 "cryptography"],
        "loop": ["coding", "security design review", "scenario",
                 "behavioural"]},
    "engineering_manager": {
        "title": "Engineering Manager", "family": "management",
        "core": ["people management", "hiring", "delivery", "stakeholder",
                 "system design", "roadmap"],
        "edge": ["org design", "performance management", "budgeting"],
        "loop": ["people / leadership", "execution", "system design",
                 "cross-functional"]},
    # ---- product, data and design
    "product_manager": {
        "title": "Product Manager", "family": "product",
        "core": ["product strategy", "roadmap", "user research",
                 "prioritization", "stakeholder", "analytics",
                 "requirements", "communication"],
        "edge": ["sql", "a/b testing", "pricing", "go-to-market",
                 "technical background", "ai products"],
        "loop": ["product sense / design", "execution and metrics",
                 "strategy", "behavioural / leadership"]},
    "data_analyst": {
        "title": "Data Analyst", "family": "data",
        "core": ["sql", "excel", "statistics", "data visualization",
                 "tableau", "communication", "business acumen"],
        "edge": ["python", "power bi", "a/b testing", "dbt", "forecasting"],
        "loop": ["SQL exercise", "case study", "take-home analysis",
                 "behavioural"]},
    "ux_designer": {
        "title": "UX / Product Designer", "family": "design",
        "core": ["user research", "wireframing", "prototyping", "figma",
                 "interaction design", "usability testing", "portfolio"],
        "edge": ["design systems", "accessibility", "motion",
                 "content design", "front-end basics"],
        "loop": ["portfolio review", "design exercise / whiteboard",
                 "cross-functional", "behavioural"]},
    "project_manager": {
        "title": "Project / Program Manager", "family": "operations",
        "core": ["planning", "scheduling", "risk management", "stakeholder",
                 "budgeting", "communication", "agile"],
        "edge": ["pmp", "scrum", "jira", "vendor management",
                 "change management"],
        "loop": ["scenario questions", "past program deep dive",
                 "stakeholder role-play", "behavioural"]},
    # ---- business
    "marketing": {
        "title": "Marketing Manager", "family": "business",
        "core": ["campaigns", "content", "seo", "analytics", "branding",
                 "copywriting", "budgeting"],
        "edge": ["paid social", "marketing automation", "crm", "a/b testing",
                 "lifecycle marketing", "product marketing"],
        "loop": ["portfolio / campaign review", "case or take-home",
                 "metrics discussion", "behavioural"]},
    "sales": {
        "title": "Sales / Account Executive", "family": "business",
        "core": ["prospecting", "negotiation", "pipeline management", "crm",
                 "closing", "communication", "quota"],
        "edge": ["salesforce", "enterprise sales", "solution selling",
                 "forecasting", "saas"],
        "loop": ["mock pitch / discovery call", "pipeline and numbers",
                 "role-play objection handling", "behavioural"]},
    "customer_success": {
        "title": "Customer Success Manager", "family": "business",
        "core": ["account management", "onboarding", "retention",
                 "communication", "crm", "problem solving"],
        "edge": ["renewals", "upselling", "saas", "health scoring",
                 "support tooling"],
        "loop": ["customer scenario role-play", "account plan exercise",
                 "behavioural"]},
    "operations": {
        "title": "Operations Manager", "family": "operations",
        "core": ["process improvement", "excel", "kpis", "supply chain",
                 "scheduling", "people management", "budgeting"],
        "edge": ["lean", "six sigma", "erp", "sql", "vendor management"],
        "loop": ["case / process scenario", "metrics deep dive",
                 "behavioural / leadership"]},
    "finance_analyst": {
        "title": "Financial Analyst", "family": "finance",
        "core": ["excel", "financial modeling", "forecasting", "accounting",
                 "budgeting", "reporting", "valuation"],
        "edge": ["sql", "power bi", "fp&a", "cfa", "python"],
        "loop": ["technical accounting / modelling questions",
                 "modelling test", "case", "behavioural"]},
    "hr_recruiting": {
        "title": "HR / Talent Acquisition", "family": "people",
        "core": ["recruiting", "sourcing", "interviewing", "employee "
                 "relations", "hris", "communication", "employment law"],
        "edge": ["people analytics", "compensation", "linkedin recruiter",
                 "dei programs", "onboarding"],
        "loop": ["scenario questions", "process walkthrough",
                 "behavioural"]},
}

# Roles a person in one role can most easily move into.
ADJACENT = {
    "backend": ["fullstack", "data_engineer", "sre_infra", "ml_engineer",
                "engineering_manager"],
    "frontend": ["fullstack", "mobile", "ux_designer"],
    "fullstack": ["backend", "frontend", "product_manager"],
    "data_engineer": ["backend", "ml_engineer", "data_analyst"],
    "ml_engineer": ["data_engineer", "backend"],
    "sre_infra": ["backend", "security"],
    "mobile": ["frontend", "fullstack"],
    "security": ["sre_infra", "backend"],
    "engineering_manager": ["product_manager", "project_manager"],
    "product_manager": ["project_manager", "ux_designer", "marketing"],
    "data_analyst": ["data_engineer", "finance_analyst", "product_manager"],
    "ux_designer": ["product_manager", "frontend"],
    "project_manager": ["product_manager", "operations"],
    "marketing": ["product_manager", "sales", "customer_success"],
    "sales": ["customer_success", "marketing"],
    "customer_success": ["sales", "project_manager", "product_manager"],
    "operations": ["project_manager", "data_analyst"],
    "finance_analyst": ["data_analyst", "operations"],
    "hr_recruiting": ["operations", "project_manager"],
}

LEVELS = {
    "junior": {"aka": ["entry", "graduate", "intern", "associate"],
               "years": "0-2", "scope": "Well-defined tasks inside a team.",
               "signals": ["Delivers assigned work with guidance",
                           "Learns fast", "Reliable follow-through"]},
    "mid": {"aka": ["intermediate"], "years": "2-5",
            "scope": "Owns projects end to end.",
            "signals": ["Plans and delivers a project",
                        "Unblocks themself",
                        "Helps teammates"]},
    "senior": {"aka": ["experienced"], "years": "5+",
               "scope": "Owns an area; influences beyond the team.",
               "signals": ["Sets direction for their area",
                           "Measurable business impact",
                           "Leads others' work", "Mentors"]},
    "staff": {"aka": ["lead", "principal", "head", "director"],
              "years": "8+",
              "scope": "Sets direction across teams.",
              "signals": ["Cross-team strategy", "Finds the right "
                          "problems", "Organisation-level results"]},
}

COMP_LEVERS = [
    "Level is the biggest lever: argue for the level with scope evidence "
    "before discussing numbers.",
    "Competing offers move numbers more than anything else. Run processes "
    "in parallel so offers land together.",
    "Negotiate the whole package: base, bonus, equity, sign-on, title, "
    "start date and flexibility.",
    "Check recent, verified pay data for your exact role, level and city "
    "(levels.fyi for tech, Glassdoor, government wage statistics, "
    "professional associations).",
    "What moves pay in most fields: measurable revenue, cost or time "
    "results; owning bigger scope; and skills in short supply in your "
    "market.",
]

RESUME_SECTIONS = {
    "junior": ["Header", "Education", "Skills", "Experience / internships",
               "Projects or volunteering"],
    "mid": ["Header + one-line tagline", "Experience", "Skills",
            "Projects or certifications (if strong)", "Education"],
    "senior": ["Header + tagline naming target role", "3-line summary",
               "Experience (most recent role gets most space)",
               "Skills grouped by area", "Education and certifications"],
    "staff": ["Header + tagline", "Summary of scope and direction",
              "Experience framed as cross-team outcomes", "Selected talks, "
              "publications or awards", "Skills", "Education"],
}

SECTION_FOCUS = {
    "junior": "Education, projects and any work experience carry weight. "
              "Show you deliver: results, numbers, links.",
    "mid": "Experience is the resume. Each bullet: what you did, the "
           "scale, the result.",
    "senior": "Ownership and impact. The first three bullets of your latest "
              "role decide the screen; lead with your biggest measurable "
              "result.",
    "staff": "Direction and leverage: problems you chose, teams you "
             "aligned, results across the organisation.",
}

# Shape of a strong bullet, with illustrative examples from several fields.
CONTRIBUTION_FRAMEWORK = {
    "formula": "Ownership verb + what you did + scale or scope + "
               "measurable result (+ how, if it adds credibility)",
    "parts": {
        "ownership": "Led, built, designed, launched, owned, created",
        "artifact": "The project, process, product or programme",
        "scale": "People, customers, accounts, sites, budget, volume",
        "result": "A number: % growth, $ saved, time cut, errors avoided",
        "how": "Key method or tool, only if it strengthens the claim",
    },
    "examples": [
        {"field": "software",
         "weak": "Worked on the checkout page.",
         "strong": "Rebuilt the checkout flow used by 40,000 customers a "
                   "month, cutting abandoned carts by 18%."},
        {"field": "sales",
         "weak": "Responsible for enterprise accounts.",
         "strong": "Closed 12 enterprise accounts worth $1.4M in new annual "
                   "revenue, 130% of quota."},
        {"field": "operations",
         "weak": "Improved warehouse processes.",
         "strong": "Redesigned picking routes across 3 warehouses, reducing "
                   "average order time from 9 to 6 minutes."},
        {"field": "healthcare",
         "weak": "Helped with patient intake.",
         "strong": "Created a triage checklist for a 25-bed unit that "
                   "reduced intake wait times by 30%."},
        {"field": "marketing",
         "weak": "Ran email campaigns.",
         "strong": "Launched a 5-email onboarding series to 60,000 users, "
                   "lifting 30-day retention by 9 points."},
    ],
    "questions": {
        "ownership": "Did you lead it, build it, or contribute? Pick the "
                     "strongest verb that is true.",
        "scale": "How big was it: people, customers, sites, budget, "
                 "volume?",
        "result": "What changed because of it? A percentage, time saved, "
                  "money made or saved, errors avoided?",
        "artifact": "What exactly did you do: name the project, process or "
                    "product.",
    },
}
