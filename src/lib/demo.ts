import type { Language, NoticeAnalysis } from "./types";

/**
 * Sample analysis shown when no backend is connected (demo mode).
 * It mirrors the shape the real /analyze endpoint must return.
 */
const en: NoticeAnalysis = {
  notice_type: "Income Tax Notice — Section 142(1)",
  authority: "National e-Assessment Centre, Income Tax Department",
  deadline: "15 November 2026",
  amount: "₹48,200 (demand shown in the notice)",
  action_required:
    "Log in to the e-filing portal, open this notice under 'Pending Actions', and either upload the requested documents or submit your reply before 15 November. Do not ignore it — non-compliance can lead to a penalty.",
  urgency_level: "high",
  scam_likelihood: "medium",
  scam_reasons: [
    "The notice arrived as an email attachment, not in your e-filing portal inbox. Genuine notices always appear there too.",
    "It asks you to pay 'immediately' through a link in the message — real demands are paid only on the official e-filing portal.",
    "No DIN (Document Identification Number) appears at the top of the notice.",
  ],
  explanation_points: [
    {
      text: "This is a request for information, not a final tax bill. The department wants details connected with your income tax return for assessment year 2025–26.",
      source_sentence: "you are hereby required to furnish the following information/documents on or before the due date.",
    },
    {
      text: "Section 142(1) gives the assessing officer the legal power to ask you for documents. You must reply within the deadline printed on the notice.",
      source_sentence: "in pursuance of section 142(1) of the Income-tax Act, 1961.",
    },
    {
      text: "The ₹48,200 shown is a preliminary calculation based on available records. It can change after your reply is reviewed.",
      source_sentence: "Total demand payable: ₹48,200 (subject to verification).",
    },
    {
      text: "If you miss the deadline, the officer can assess your income on his own estimate and may impose a penalty for non-compliance.",
      source_sentence: "Non-compliance may attract penal action under section 271(1)(b) of the Act.",
    },
  ],
  raw_text: [
    "GOVERNMENT OF INDIA / INCOME TAX DEPARTMENT",
    "OFFICE OF THE ASSESSING OFFICER, NPCI, DELHI",
    "NOTICE u/s 142(1) OF THE INCOME-TAX ACT, 1961",
    "",
    "PAN: ABCDE1234F    AY: 2025-26",
    "",
    "Whereas you are hereby required to furnish the following information/documents on or before the due date, in pursuance of section 142(1) of the Income-tax Act, 1961:",
    "1. Copies of bank statements for the period 01/04/2024 to 31/03/2025.",
    "2. Details of all high-value transactions reported by SFT.",
    "",
    "Total demand payable: ₹48,200 (subject to verification).",
    "Non-compliance may attract penal action under section 271(1)(b) of the Act.",
    "",
    "Deputy Commissioner of Income Tax, Circle 12(1), New Delhi",
  ].join("\n"),
  helpline: { name: "Aaykar Sampark Kendra", number: "1800-180-1961" },
  is_high_risk: true,
};

const hi: NoticeAnalysis = {
  notice_type: "आयकर नोटिस — धारा 142(1)",
  authority: "राष्ट्रीय ई-आकलन केंद्र, आयकर विभाग",
  deadline: "15 नवम्बर 2026",
  amount: "₹48,200 (नोटिस में दिखी माँग)",
  action_required:
    "ई-फ़ाइलिंग पोर्टल पर लॉगिन करें, 'Pending Actions' में यह नोटिस खोलें, और 15 नवम्बर से पहले माँगे गए दस्तावेज़ अपलोड करें या जवाब भेजें। नोटिस को नज़रअंदाज़ न करें — इससे जुर्माना लग सकता है।",
  urgency_level: "high",
  scam_likelihood: "medium",
  scam_reasons: [
    "नोटिस ईमेल के अटैचमेंट के रूप में आया है, ई-फ़ाइलिंग पोर्टल के इनबॉक्स में नहीं। असली नोटिस वहाँ भी दिखते हैं।",
    "इसमें संदेश के अंदर लिंक से 'तुरंत भुगतान' करने को कहा गया है — असली माँग केवल आधिकारिक ई-फ़ाइलिंग पोर्टल पर चुकाई जाती है।",
    "नोटिस के ऊपर कोई DIN (दस्तावेज़ पहचान संख्या) नहीं है।",
  ],
  explanation_points: [
    {
      text: "यह जानकारी माँगने का नोटिस है, कोई अंतिम कर-बिल नहीं। विभाग आपके आयकर रिटर्न (आकलन वर्ष 2025–26) से जुड़े ब्यौरे चाहता है।",
      source_sentence: "you are hereby required to furnish the following information/documents on or before the due date.",
    },
    {
      text: "धारा 142(1) आकलन अधिकारी को दस्तावेज़ माँगने की कानूनी शक्ति देती है। आपको नोटिस पर छपी अंतिम तारीख तक जवाब देना होगा।",
      source_sentence: "in pursuance of section 142(1) of the Income-tax Act, 1961.",
    },
    {
      text: "दिखी ₹48,200 उपलब्ध रिकॉर्ड के आधार पर प्रारंभिक हिसाब है। आपके जवाब की समीक्षा के बाद यह बदल सकती है।",
      source_sentence: "Total demand payable: ₹48,200 (subject to verification).",
    },
    {
      text: "अंतिम तारीख छूट गई तो अधिकारी अपने अनुमान पर आय आकलित कर सकता है और ग़ैर-अनुपालन का जुर्माना लगा सकता है।",
      source_sentence: "Non-compliance may attract penal action under section 271(1)(b) of the Act.",
    },
  ],
  raw_text: en.raw_text,
  helpline: { name: "आयकर संपर्क केंद्र", number: "1800-180-1961" },
  is_high_risk: true,
};

export function demoAnalysis(language: Language): NoticeAnalysis {
  const base = language === "hi" ? hi : en;
  return { ...base, is_demo: true };
}
