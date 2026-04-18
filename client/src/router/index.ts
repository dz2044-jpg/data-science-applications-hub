import { createRouter, createWebHistory } from 'vue-router';

import MainLayout from '@/layouts/MainLayout.vue';
import HubCentralSetup from '@/pages/HubCentralSetup.vue';
import BinaryFeatureAnalysisPage from '@/modules/binary-feature-ae/pages/BinaryFeatureAnalysisPage.vue';
import MortalityAeAnalysisPage from '@/modules/mortality-ae/pages/MortalityAeAnalysisPage.vue';

export const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: '/',
            component: MainLayout,
            children: [
                {
                    path: '',
                    component: HubCentralSetup,
                },
                {
                    path: 'mortality-ae',
                    redirect: '/mortality-ae/analysis',
                },
                {
                    path: 'mortality-ae/analysis',
                    component: MortalityAeAnalysisPage,
                },
                {
                    path: 'binary-feature-ae',
                    redirect: '/binary-feature-ae/analysis',
                },
                {
                    path: 'binary-feature-ae/analysis',
                    component: BinaryFeatureAnalysisPage,
                },
            ],
        },
    ],
});
