import json
import os
import threading
from backend.config import KB_DATA_PATH

_lock = threading.Lock()

_DEFAULT_KB = {
    "institute": {
        "name": "European IT Solutions Institute",
        "address": "Noor Mansion (3rd Floor), Plot#04, Main Road#01, Mirpur-10, Dhaka-1216",
        "phone": "+8801889977951",
        "hours": "Monday to Sunday, 10 AM to 9 PM",
        "facilities": [
            "Industry-relevant curriculum matched to current market needs",
            "Expert mentors with real-world professional experience",
            "Hands-on, project-based training",
            "Career support: portfolio, interview prep, freelancing guidance",
            "Both online and offline (in-person) class formats",
            "ISO certified, NSDA accredited, and a member of BASIS, BCS, BACCO, and BWCCI",
        ],
        "extra_info": [
            "২০০৯ সালে আয়ারল্যান্ড, জার্মানি ও বাংলাদেশে আইটি ও ওয়েব সল্যুশনস কোম্পানি হিসেবে যাত্রা শুরু",
            "১৫+ বছরের অভিজ্ঞতা, ৮০,০০০+ শিক্ষার্থীকে প্রশিক্ষণ দেওয়া হয়েছে",
            "২৪/৭ অনলাইন সাপোর্ট এবং কোর্স শেষেও লাইফটাইম মেন্টর সাপোর্ট",
            "সুসজ্জিত প্র্যাকটিস ল্যাব — নির্ধারিত ক্লাসের বাইরেও অনুশীলনের সুযোগ",
            "প্রতিটি ক্লাস রেকর্ড করা হয়, মিস করলে ভিডিও দেখে ক্যাচ-আপ করা যায়",
            "নিয়মিত রিভিউ ক্লাস আয়োজন করা হয় দুর্বল জায়গা ঝালিয়ে নেওয়ার জন্য",
            "নিজস্ব জব প্লেসমেন্ট সেল আছে — সিভি তৈরি, ইন্টারভিউ প্রস্তুতি, ফ্রিল্যান্সিং গাইডলাইন",
            "পেমেন্ট করা যায় bKash, Nagad ও SSLCommerz-এর মাধ্যমে",
            "যোগাযোগ: +8801889977951 / +8801889977952, help@europeanit-inst.com",
        ],
    },
    "calling_reason": (
        "এই লিডরা ওয়েবসাইটে বা ফেসবুক ফর্মে একটি কোর্সে ভর্তি সংক্রান্ত আগ্রহ দেখিয়েছেন "
        "(অ্যাডমিশন ফর্ম পূরণ করেছেন বা ডেমো ক্লাসের জন্য রিকোয়েস্ট করেছেন) কিন্তু এখনো "
        "পেমেন্ট করে ভর্তি সম্পন্ন করেননি।"
    ),
    "terms": [
        "ভর্তির ৭-১০ দিনের মধ্যে রিফান্ড রিকোয়েস্ট জানাতে হবে",
        "রিকোয়েস্ট গৃহীত হলে ১০ দিনের মধ্যে রিফান্ড সম্পন্ন হয়",
        "রিফান্ড মূল পেমেন্ট পদ্ধতিতে অথবা রিফান্ড ক্রেডিট হিসেবে দেওয়া হতে পারে, প্রতিষ্ঠানের সিদ্ধান্ত অনুযায়ী",
    ],
    "courses": {
        "digital_marketing": {"name": "AI And Data Driven Digital Marketing", "price": "৳4,999 - ৳15,000"},
        "web_design": {"name": "Web Design & Development with WordPress", "price": "৳5,000 - ৳15,000"},
        "graphic_design": {"name": "Income and AI Focus Graphic Design", "price": "৳4,999 - ৳15,000"},
        "ui_ux": {"name": "Income and AI Focus UI/UX Design", "price": "৳4,999 - ৳15,000"},
        "video_editing": {
            "name": "Video Editing & Motion Graphics with AI Certificate",
            "price": "৳15,000 (Online, 3 মাস, 24 ক্লাস) - ৳20,000 (Offline, 4 মাস, 32 ক্লাস)",
        },
        "basic_computer": {
            "name": "Basic Computer with AI Mastery Course",
            "price": "৳1,999 (Online, 3 মাস, 24 ক্লাস) - ৳5,000 (Offline, 4 মাস, 32 ক্লাস)",
        },
        "seo": {
            "name": "AI-Powered SEO Mastery Course",
            "price": "৳8,000 (Online, 3 মাস, 24 ক্লাস) - ৳11,000 (Offline, 4 মাস, 32 ক্লাস)",
        },
        "facebook_ads": {"name": "Practical Facebook Ads Mastery", "price": "৳4,999 - ৳15,000"},
        "python_django": {"name": "Python Development with Django", "price": "৳15,000 - ৳22,500"},
        "data_analytics": {"name": "Data Analytics & Machine Learning with Python", "price": "৳15,000 - ৳22,500"},
    },
}


def _load() -> dict:
    if not os.path.exists(KB_DATA_PATH):
        _save(_DEFAULT_KB)
        return json.loads(json.dumps(_DEFAULT_KB))
    with open(KB_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(kb: dict):
    with open(KB_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(kb, f, ensure_ascii=False, indent=2)


def get_kb() -> dict:
    with _lock:
        return _load()


def get_courses() -> dict:
    return get_kb()["courses"]


def update_institute(data: dict) -> dict:
    with _lock:
        kb = _load()
        kb["institute"].update(data)
        _save(kb)
        return kb["institute"]


def update_calling_reason(text: str) -> str:
    with _lock:
        kb = _load()
        kb["calling_reason"] = text
        _save(kb)
        return kb["calling_reason"]


def update_terms(terms: list[str]) -> list[str]:
    with _lock:
        kb = _load()
        kb["terms"] = terms
        _save(kb)
        return kb["terms"]


def add_course(key: str, name: str, price: str) -> dict:
    with _lock:
        kb = _load()
        if key in kb["courses"]:
            raise ValueError(f"Course key '{key}' already exists")
        kb["courses"][key] = {"name": name, "price": price}
        _save(kb)
        return kb["courses"][key]


def update_course(key: str, name: str | None = None, price: str | None = None) -> dict:
    with _lock:
        kb = _load()
        if key not in kb["courses"]:
            raise KeyError(key)
        if name is not None:
            kb["courses"][key]["name"] = name
        if price is not None:
            kb["courses"][key]["price"] = price
        _save(kb)
        return kb["courses"][key]


def delete_course(key: str):
    with _lock:
        kb = _load()
        if key not in kb["courses"]:
            raise KeyError(key)
        del kb["courses"][key]
        _save(kb)


def build_system_prompt(lead_name: str, course_key: str) -> str:
    kb = get_kb()
    institute = kb["institute"]
    course = kb["courses"][course_key]
    calling_reason = kb["calling_reason"]
    terms_bullets = "\n".join(f"- {t}" for t in kb["terms"])

    return f"""তুমি {institute['name']}-এর একজন স্মার্ট AI কল সেন্টার এজেন্ট। তোমার নাম "মিতা"।
তুমি {lead_name}-কে কল করছ "{course['name']}" কোর্সে ভর্তি নিশ্চিত করার জন্য।
কোর্সের ফি: {course['price']}।

কল করার প্রেক্ষাপট: {calling_reason}

**প্রথম বাক্যে যা যা থাকতে হবে (এই ক্রমে, বিনয়ী ও মার্কেটিং-বান্ধব সুরে):**
1. নিজের নাম "মিতা" বলে সালাম/শুভেচ্ছা জানাও।
2. বিনীতভাবে জানাও যে তুমি একটি AI স্মার্ট অ্যাসিস্ট্যান্ট — যেমন: "আমি {institute['name']}-এর একটি AI স্মার্ট অ্যাসিস্ট্যান্ট, আপনার সাথে কথা বলতে পেরে ভালো লাগছে।"
3. খুব সংক্ষেপে ও হাসিমুখে বলো যে মাঝে মাঝে উত্তর দিতে একটু সময় লাগতে পারে, তাই একটু ধৈর্য ধরার জন্য অনুরোধ করো — যেমন: "মাঝে মাঝে উত্তর দিতে একটু সময় লাগতে পারে, দয়া করে একটু ধৈর্য ধরবেন।"
4. এরপর {calling_reason}-এর প্রেক্ষাপটে কল করার কারণ বলো।

উদাহরণ (টোন বোঝার জন্য, হুবহু কপি করার দরকার নেই):
"আসসালামু আলাইকুম, আমি মিতা, {institute['name']}-এর একটি AI স্মার্ট অ্যাসিস্ট্যান্ট। আপনার সাথে কথা বলতে পেরে ভালো লাগছে। মাঝে মাঝে উত্তর দিতে একটু সময় লাগতে পারে, দয়া করে একটু ধৈর্য ধরবেন। আপনি আমাদের '{course['name']}' কোর্সে আগ্রহ দেখিয়েছিলেন, তাই একটু খোঁজ নিতে কল করলাম।"

প্রতিষ্ঠান সম্পর্কে (যদি জিজ্ঞেস করা হয়):
- ঠিকানা: {institute['address']}
- ক্লাস অনলাইন ও অফলাইন দুই ফরম্যাটেই পাওয়া যায়
- এক্সপার্ট মেন্টর, হাতে-কলমে প্রজেক্ট ভিত্তিক প্রশিক্ষণ
- ক্যারিয়ার সাপোর্ট: পোর্টফোলিও, ইন্টারভিউ প্রস্তুতি, ফ্রিল্যান্সিং গাইডেন্স
- ISO সার্টিফায়েড, NSDA স্বীকৃত

পেমেন্ট ও রিফান্ড শর্তাবলী (যদি জিজ্ঞেস করা হয়):
{terms_bullets}

নিয়ম:
1. সবসময় স্বাভাবিক, বিনয়ী বাংলায় কথা বল, ছোট ছোট বাক্যে।
2. প্রথমেই নিজের পরিচয়, তুমি যে একটি AI স্মার্ট অ্যাসিস্ট্যান্ট তা এবং কল করার কারণ বল (উপরের নির্দেশনা অনুযায়ী)।
3. লিড কোর্সে ভর্তি হতে চায় কিনা জিজ্ঞেস কর।
4. কেউ সুবিধা-অসুবিধা জিজ্ঞেস করলে উপরের তথ্য দিয়ে উত্তর দাও।
5. উত্তর দিতে দেরি হলে বা লিড কিছু আবার বলতে বললে, বিরক্ত না হয়ে হাসিমুখে আবার ভদ্রভাবে বলো।
6. কথোপকথনের শেষে, ফলাফল যাই হোক না কেন, সময় দেওয়ার জন্য বিনীতভাবে ধন্যবাদ জানাও।

**অত্যন্ত গুরুত্বপূর্ণ — প্রতিটি উত্তরের একদম শেষে, একটি নতুন লাইনে, ঠিক এই ফরম্যাটে স্ট্যাটাস লিখতে হবে:**
STATUS: undecided
অথবা STATUS: interested
অথবা STATUS: not_interested
অথবা STATUS: callback_requested

লিড স্পষ্টভাবে সম্মত না হওয়া পর্যন্ত STATUS: undecided লিখবে।
"""