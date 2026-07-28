"""
skills_db.py
------------
A reference database of known skills used for skill extraction from
resume and job description text.

Each skill maps to a list of variants/abbreviations that should also
be recognized as that same skill (e.g. "JS" should count as "JavaScript").

This is intentionally a flat, explicit dictionary rather than a trained
model — it's easy to extend, fully explainable, and doesn't require
any training data. Good enough coverage for common tech roles; extend
the lists below as you test against more resumes/JDs.
"""

SKILLS_DB = {
    # Programming languages
    "Python": ["python"],
    "JavaScript": ["javascript", "js"],
    "TypeScript": ["typescript", "ts"],
    "Java": ["java"],
    "C++": ["c++", "cpp"],
    "C#": ["c#", "csharp"],
    "Go": ["golang", "go"],
    "Rust": ["rust"],
    "Ruby": ["ruby"],
    "PHP": ["php"],
    "SQL": ["sql"],

    # Web frameworks
    "Django": ["django"],
    "Flask": ["flask"],
    "FastAPI": ["fastapi"],
    "React": ["react", "react.js", "reactjs"],
    "Angular": ["angular"],
    "Vue.js": ["vue", "vue.js", "vuejs"],
    "Node.js": ["node", "node.js", "nodejs"],
    "Express": ["express", "express.js"],

    # Databases
    "PostgreSQL": ["postgresql", "postgres"],
    "MySQL": ["mysql"],
    "MongoDB": ["mongodb", "mongo"],
    "Redis": ["redis"],
    "SQLite": ["sqlite"],

    # Cloud / DevOps
    "AWS": ["aws", "amazon web services"],
    "Azure": ["azure"],
    "GCP": ["gcp", "google cloud", "google cloud platform"],
    "Docker": ["docker"],
    "Kubernetes": ["kubernetes", "k8s"],
    "CI/CD": ["ci/cd", "ci-cd", "continuous integration", "continuous deployment"],
    "Git": ["git"],
    "Linux": ["linux"],

    # Concepts
    "REST APIs": ["rest api", "rest apis", "restful api", "restful apis"],
    "Microservices": ["microservices", "microservice architecture"],
    "Machine Learning": ["machine learning", "ml", "ai/ml"],
    "Deep Learning": ["deep learning", "dl"],
    "NLP": ["nlp", "natural language processing"],
    "Data Analysis": ["data analysis"],
    "Distributed Systems": ["distributed systems", "distributed computing"],
    "System Design": ["system design"],
    "Data Structures": ["data structures"],
    "Algorithms": ["algorithms", "algorithm design"],
    "Agentic AI": ["agentic ai", "ai agents", "multi-agent"],
    "OpenStack": ["openstack"],
    "Ceph": ["ceph"],

    # Tools
    "Excel": ["excel", "ms excel", "microsoft excel"],
    "Tableau": ["tableau"],
    "Power BI": ["power bi", "powerbi"],
    "Pandas": ["pandas"],
    "NumPy": ["numpy"],

    # Soft skills
    "Communication": ["communication", "communication skills"],
    "Leadership": ["leadership"],
    "Teamwork": ["teamwork", "team collaboration"],
    "Problem Solving": ["problem solving", "problem-solving"],
    "Customer Support": ["customer support", "customer service"],

    # Office / admin / clerical
    "MS Word": ["ms word", "microsoft word"],
    "Data Entry": ["data entry"],
    "Typing": ["typing"],
    "Filing Systems": ["filing systems", "filing"],
    "Record Keeping": ["record keeping", "recordkeeping", "records management"],
    "Email Correspondence": ["email correspondence", "email management"],
    "Scheduling": ["scheduling", "calendar management"],
    "Documentation": ["documentation"],
    "Office Administration": ["office administration", "office coordination", "administrative support"],
}
