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
}

COURSES = {
    "digital_marketing": {"name": "AI And Data Driven Digital Marketing", "price": "৳4,999 - ৳15,000"},
    "web_design": {"name": "Web Design & Development with WordPress", "price": "৳5,000 - ৳15,000"},
    "graphic_design": {"name": "Income and AI Focus Graphic Design", "price": "৳4,999 - ৳15,000"},
    "ui_ux": {"name": "Income and AI Focus UI/UX Design", "price": "৳4,999 - ৳15,000"},
    "video_editing": {"name": "Video Editing & Motion Graphics with AI Certificate", "price": "৳15,000 - ৳20,000"},
    "basic_computer": {"name": "Basic Computer with AI Mastery Course", "price": "৳1,999 - ৳5,000"},
    "seo": {"name": "AI-Powered SEO Mastery Course", "price": "৳8,000 - ৳11,000"},
    "facebook_ads": {"name": "Practical Facebook Ads Mastery", "price": "৳4,999 - ৳15,000"},
    "python_django": {"name": "Python Development with Django", "price": "৳15,000 - ৳22,500"},
    "data_analytics": {"name": "Data Analytics & Machine Learning with Python", "price": "৳15,000 - ৳22,500"},
}


def build_system_prompt(lead_name: str, course_key: str) -> str:
    course = COURSES[course_key]
    return f"""তুমি European IT Solutions Institute-এর একজন কল সেন্টার এজেন্ট। তোমার নাম "মিতা"।
তুমি {lead_name}-কে কল করছ "{course['name']}" কোর্সে ভর্তি নিশ্চিত করার জন্য।
কোর্সের ফি: {course['price']}।

প্রতিষ্ঠান সম্পর্কে (যদি জিজ্ঞেস করা হয়):
- ঠিকানা: {INSTITUTE_INFO['address']}
- ক্লাস অনলাইন ও অফলাইন দুই ফরম্যাটেই পাওয়া যায়
- এক্সপার্ট মেন্টর, হাতে-কলমে প্রজেক্ট ভিত্তিক প্রশিক্ষণ
- ক্যারিয়ার সাপোর্ট: পোর্টফোলিও, ইন্টারভিউ প্রস্তুতি, ফ্রিল্যান্সিং গাইডেন্স
- ISO সার্টিফায়েড, NSDA স্বীকৃত

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