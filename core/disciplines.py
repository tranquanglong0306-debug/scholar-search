# core/disciplines.py
# Định nghĩa các ngành học/lĩnh vực và từ khóa gợi ý tương ứng để biến ScholarSearch thành ứng dụng đa ngành.

DISCIPLINES = {
    "Ngôn ngữ học ứng dụng & Ngoại ngữ": [
        "task-based language teaching",
        "second language acquisition",
        "EFL vocabulary learning",
        "communicative language teaching",
        "language assessment",
        "computer-assisted language learning",
        "extensive reading",
        "writing instruction EFL",
        "language anxiety classroom",
        "motivation language learning"
    ],
    "Giáo dục & Sư phạm": [
        "active learning pedagogy",
        "blended learning in higher education",
        "flipped classroom effectiveness",
        "stem education k-12",
        "project-based learning classroom",
        "inclusive education strategies",
        "teacher professional development",
        "educational technology integration",
        "student engagement online learning",
        "formative assessment classroom"
    ],
    "Khoa học máy tính & CNTT": [
        "large language models",
        "deep learning neural networks",
        "blockchain secure smart contracts",
        "internet of things iot security",
        "natural language processing nlp",
        "cloud computing architecture",
        "computer vision image recognition",
        "cybersecurity threat detection",
        "generative artificial intelligence",
        "human-computer interaction"
    ],
    "Kinh tế & Quản trị kinh doanh": [
        "digital marketing consumer behavior",
        "corporate social responsibility csr",
        "supply chain resilience logistics",
        "financial technology fintech services",
        "e-commerce adoption factors",
        "organizational culture productivity",
        "entrepreneurship startup success",
        "circular economy business models",
        "inflation monetary policy",
        "sustainable investing esg"
    ],
    "Y học & Khoa học sức khỏe": [
        "personalized medicine oncology",
        "mrna vaccines immunology",
        "mental health anxiety covid-19",
        "telemedicine patient outcomes",
        "cardiovascular disease risk factors",
        "diabetes mellitus management",
        "public health epidemiology",
        "nutrition dietary patterns",
        "physical activity health benefits",
        "healthcare system efficiency"
    ],
    "Khoa học xã hội & Nhân văn": [
        "gender studies equality",
        "cultural representation identity",
        "social media public opinion",
        "urban sociology gentrification",
        "psychological impact remote work",
        "climate change communication",
        "ethics artificial intelligence",
        "historical analysis colonialism",
        "globalization cultural impact",
        "migration refugee studies"
    ],
    "Môi trường & Sinh thái": [
        "renewable energy transition solar",
        "climate change adaptation mitigation",
        "biodiversity conservation planning",
        "microplastics marine pollution",
        "sustainable agriculture soil health",
        "deforestation carbon sequestration",
        "waste management recycling",
        "water resources sustainability",
        "air quality health impact",
        "urban green infrastructure"
    ],
    "Ngành học / Lĩnh vực khác": [
        "research methodology",
        "literature review",
        "data analysis techniques",
        "scientific writing",
        "mixed methods study",
        "statistical significance",
        "qualitative research design",
        "quantitative analysis",
        "academic integrity publication",
        "interdisciplinary study"
    ]
}

def get_disciplines_list() -> list:
    """Trả về danh sách các ngành học/lĩnh vực."""
    return list(DISCIPLINES.keys())

def get_keywords_by_discipline(discipline: str) -> list:
    """Trả về danh sách từ khóa gợi ý của một ngành học."""
    return DISCIPLINES.get(discipline, [])
