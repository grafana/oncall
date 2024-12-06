import i18next from 'i18next';
import { initReactI18next } from 'react-i18next';
import english from './lang/en.json';
import italian from './lang/it.json';

i18next
    .use(initReactI18next)
    .init({
        resources: {
            en: { translation: english },
            it: { translation: italian },
        },
        supportedLngs: ['en', 'it'],
        interpolation: { escapeValue: false },
        lng: navigator.language.split('-')[0], //browser language
        fallbackLng: 'en', //default
        default: false,
    })

export default i18next