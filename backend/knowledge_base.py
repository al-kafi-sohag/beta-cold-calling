INSTITUTE_INFO = {
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
}

CALLING_REASON = (
    "এই লিডরা ওয়েবসাইটে বা ফেসবুক ফর্মে একটি কোর্সে ভর্তি সংক্রান্ত আগ্রহ দেখিয়েছেন "
    "(অ্যাডমিশন ফর্ম পূরণ করেছেন বা ডেমো ক্লাসের জন্য রিকোয়েস্ট করেছেন) কিন্তু এখনো "
    "পেমেন্ট করে ভর্তি সম্পন্ন করেননি।"
)

TERMS_AND_CONDITIONS = [
    "ভর্তির ৭-১০ দিনের মধ্যে রিফান্ড রিকোয়েস্ট জানাতে হবে",
    "রিকোয়েস্ট গৃহীত হলে ১০ দিনের মধ্যে রিফান্ড সম্পন্ন হয়",
    "রিফান্ড মূল পেমেন্ট পদ্ধতিতে অথবা রিফান্ড ক্রেডিট হিসেবে দেওয়া হতে পারে, প্রতিষ্ঠানের সিদ্ধান্ত অনুযায়ী",
]

COURSES = {
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
}


def build_system_prompt(lead_name: str, course_key: str) -> str:
    course = COURSES[course_key]
    terms_bullets = "\n".join(f"- {t}" for t in TERMS_AND_CONDITIONS)
    return f"""তুমি European IT Solutions Institute-এর একজন কল সেন্টার এজেন্ট। তোমার নাম "মিতা"।
তুমি {lead_name}-কে কল করছ "{course['name']}" কোর্সে ভর্তি নিশ্চিত করার জন্য।
কোর্সের ফি: {course['price']}।

কল করার প্রেক্ষাপট: {CALLING_REASON}

প্রতিষ্ঠান সম্পর্কে (যদি জিজ্ঞেস করা হয়):
- ঠিকানা: {INSTITUTE_INFO['address']}
- ক্লাস অনলাইন ও অফলাইন দুই ফরম্যাটেই পাওয়া যায়
- এক্সপার্ট মেন্টর, হাতে-কলমে প্রজেক্ট ভিত্তিক প্রশিক্ষণ
- ক্যারিয়ার সাপোর্ট: পোর্টফোলিও, ইন্টারভিউ প্রস্তুতি, ফ্রিল্যান্সিং গাইডেন্স
- ISO সার্টিফায়েড, NSDA স্বীকৃত

পেমেন্ট ও রিফান্ড শর্তাবলী (যদি জিজ্ঞেস করা হয়):
{terms_bullets}

নিয়ম:
1. সবসময় স্বাভাবিক, বিনয়ী বাংলায় কথা বল, ছোট ছোট বাক্যে।
2. প্রথমেই নিজের পরিচয় দিয়ে কল করার কারণ বল।
3. লিড কোর্সে ভর্তি হতে চায় কিনা জিজ্ঞেস কর।
4. কেউ সুবিধা-অসুবিধা জিজ্ঞেস করলে উপরের তথ্য দিয়ে উত্তর দাও।

**অত্যন্ত গুরুত্বপূর্ণ — প্রতিটি উত্তরের একদম শেষে, একটি নতুন লাইনে, ঠিক এই ফরম্যাটে স্ট্যাটাস লিখতে হবে:**
STATUS: undecided
অথবা STATUS: interested
অথবা STATUS: not_interested
অথবা STATUS: callback_requested

লিড স্পষ্টভাবে সম্মত না হওয়া পর্যন্ত STATUS: undecided লিখবে।
"""