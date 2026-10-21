import type { Language } from "./types";

const en = {
  appTitle: "Notice Saathi",
  tagline: "Upload a government notice. Get it explained in plain words.",
  uploadTitle: "Upload your notice",
  uploadHint: "JPG, PNG or PDF, up to 10 MB. Your file is used only to prepare the explanation.",
  uploadButton: "Choose file",
  dropHint: "or drag & drop it here",
  analyzing: "Reading your notice carefully…",
  analyzeError: "We couldn't read that notice. Please try again with a clearer photo or a PDF.",
  whatItMeans: "What this notice means",
  whatToDo: "What you need to do",
  deadline: "Deadline",
  amount: "Amount involved",
  authority: "Issued by",
  noticeType: "Notice type",
  urgencyHigh: "Act quickly",
  urgencyMedium: "Needs attention",
  urgencyLow: "Not urgent",
  scamWarningTitle: "Warning signs of a fake notice",
  listen: "Listen to this",
  stopListening: "Stop",
  addReminder: "Add reminder to calendar",
  viewSource: "Show source line",
  hideSource: "Hide source line",
  notLegalAdvice:
    "This notice looks serious. Consider consulting a lawyer or a chartered accountant before responding. This explanation is not legal advice.",
  helpline: "Official helpline",
  startOver: "Analyze another notice",
  switchLang: "Switch language",
  fileTooLarge: "That file is larger than 10 MB.",
  fileWrongType: "Only JPG, PNG and PDF files are supported.",
  keyFacts: "Key facts",
  timeoutError: "The analysis took too long to respond. Please try again.",
  offlineError: "Check your internet connection and try again.",
  noExplanationPoints: "No specific explanation points could be derived from this notice.",
};

type Strings = typeof en;

const hi: Strings = {
  appTitle: "नोटिस साथी",
  tagline: "कोई भी सरकारी नोटिस अपलोड करें। आसान भाषा में समझ पाएं।",
  uploadTitle: "अपना नोटिस अपलोड करें",
  uploadHint: "JPG, PNG या PDF, 10 MB तक। आपकी फ़ाइल केवल समझाने के काम में आती है।",
  uploadButton: "फ़ाइल चुनें",
  dropHint: "या यहाँ खींचकर छोड़ें",
  analyzing: "आपका नोटिस ध्यान से पढ़ा जा रहा है…",
  analyzeError: "यह नोटिस पढ़ा नहीं जा सका। कृपया साफ़ तस्वीर या PDF से फिर कोशिश करें।",
  whatItMeans: "इस नोटिस का मतलब क्या है",
  whatToDo: "आपको क्या करना है",
  deadline: "अंतिम तारीख",
  amount: "राशि",
  authority: "जारीकर्ता",
  noticeType: "नोटिस का प्रकार",
  urgencyHigh: "जल्दी काम करें",
  urgencyMedium: "ध्यान देना ज़रूरी",
  urgencyLow: "जल्दी नहीं",
  scamWarningTitle: "नकली नोटिस के खतरे के संकेत",
  listen: "सुनें",
  stopListening: "रोकें",
  addReminder: "कैलेंडर में रिमाइंडर जोड़ें",
  viewSource: "मूल पंक्ति देखें",
  hideSource: "मूल पंक्ति छिपाएँ",
  notLegalAdvice:
    "यह नोटिस गंभीर लगता है। जवाब देने से पहले किसी वकील या सीए से सलाह लें। यह समझाना कानूनी सलाह नहीं है।",
  helpline: "आधिकारिक हेल्पलाइन",
  startOver: "दूसरा नोटिस जाँचें",
  switchLang: "भाषा बदलें",
  fileTooLarge: "यह फ़ाइल 10 MB से बड़ी है।",
  fileWrongType: "केवल JPG, PNG और PDF फ़ाइलें चलेंगी।",
  keyFacts: "मुख्य बातें",
  timeoutError: "विश्लेषण में बहुत अधिक समय लगा। कृपया पुनः प्रयास करें।",
  offlineError: "कृपया अपना इंटरनेट कनेक्शन जाँचें और पुनः प्रयास करें।",
  noExplanationPoints: "इस नोटिस के लिए कोई विशिष्ट बिंदु उपलब्ध नहीं हैं।",
};

const strings: Record<Language, Strings> = { en, hi };

export type StringKey = keyof Strings;

export function t(language: Language, key: StringKey): string {
  return strings[language][key];
}
