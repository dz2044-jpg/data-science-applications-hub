import { createApp } from 'vue';
import { Dialog, Notify, Quasar } from 'quasar';
import quasarIconSet from 'quasar/icon-set/material-icons';
import quasarLang from 'quasar/lang/en-US';

import 'quasar/src/css/index.sass';
import '@quasar/extras/material-icons/material-icons.css';

import App from './App.vue';
import { router } from './router';

createApp(App)
    .use(Quasar, {
        plugins: {
            Notify,
            Dialog,
        },
        lang: quasarLang,
        iconSet: quasarIconSet,
    })
    .use(router)
    .mount('#app');

