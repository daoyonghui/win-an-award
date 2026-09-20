<script setup>
import { useRouter } from 'vue-router'
import { lang, setLang, t } from '../i18n/useLanguage'
import { demoMode, motion, setDemoMode, setMotion, setShowTips, showTips } from '../settings'

const router = useRouter()
</script>

<template>
  <main class="settings">
    <header class="head">
      <h1 class="section-title">{{ t('settings.title') }}</h1>
      <p class="subtitle">{{ t('settings.subtitle') }}</p>
    </header>

    <div class="group">
      <!-- 语言 -->
      <div class="row">
        <div class="row-left">
          <span class="row-label">{{ t('settings.language') }}</span>
        </div>
        <div class="segmented" role="group">
          <button
            type="button"
            :class="{ active: lang === 'zh' }"
            @click="setLang('zh')"
          >
            {{ t('settings.language.zh') }}
          </button>
          <button
            type="button"
            :class="{ active: lang === 'en' }"
            @click="setLang('en')"
          >
            {{ t('settings.language.en') }}
          </button>
        </div>
      </div>

      <!-- 动画效果 -->
      <div class="row">
        <div class="row-left">
          <span class="row-label">{{ t('settings.motion') }}</span>
        </div>
        <div class="segmented" role="group">
          <button
            type="button"
            :class="{ active: motion === 'standard' }"
            @click="setMotion('standard')"
          >
            {{ t('settings.motion.standard') }}
          </button>
          <button
            type="button"
            :class="{ active: motion === 'reduced' }"
            @click="setMotion('reduced')"
          >
            {{ t('settings.motion.reduced') }}
          </button>
        </div>
      </div>

      <!-- 新手提示 -->
      <div class="row">
        <div class="row-left">
          <span class="row-label">{{ t('settings.tips') }}</span>
        </div>
        <div class="segmented" role="group">
          <button
            type="button"
            :class="{ active: showTips }"
            @click="setShowTips(true)"
          >
            {{ t('settings.tips.show') }}
          </button>
          <button
            type="button"
            :class="{ active: !showTips }"
            @click="setShowTips(false)"
          >
            {{ t('settings.tips.hide') }}
          </button>
        </div>
      </div>

      <!-- 演示模式 -->
      <div class="row">
        <div class="row-left">
          <span class="row-label">{{ t('settings.demo') }}</span>
        </div>
        <div class="segmented" role="group">
          <button
            type="button"
            :class="{ active: demoMode }"
            @click="setDemoMode(true)"
          >
            {{ t('settings.on') }}
          </button>
          <button
            type="button"
            :class="{ active: !demoMode }"
            @click="setDemoMode(false)"
          >
            {{ t('settings.off') }}
          </button>
        </div>
      </div>
    </div>

    <!-- 关于 -->
    <section class="about">
      <h2 class="about-title">{{ t('settings.about') }}</h2>
      <div class="about-row">
        <span class="about-k">{{ t('settings.version') }}</span>
        <span class="about-v">PrintMind V1.2</span>
      </div>
      <div class="about-row">
        <span class="about-k">{{ t('settings.project') }}</span>
        <span class="about-v">{{ t('settings.project.value') }}</span>
      </div>
      <button class="btn" type="button" @click="router.push('/tribute')">
        {{ t('settings.tribute') }}
      </button>
      <button v-if="demoMode" class="btn" type="button" @click="router.push('/demo-offline')">
        {{ t('nav.demoOffline') }}
      </button>
    </section>
  </main>
</template>

<style scoped>
.settings {
  max-width: 960px;
  margin: 0 auto;
  padding: 4rem 2rem 6rem;
  display: flex;
  flex-direction: column;
  gap: 3rem;
}

.head {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.subtitle {
  margin: 0;
  color: var(--text-2);
  font-size: 1.02rem;
}

.group {
  border-top: 1px solid var(--border);
}

.row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
  padding: 1.25rem 0.75rem;
  border-bottom: 1px solid var(--border);
  transition: background 0.18s var(--ease);
}

.row:hover {
  background: rgba(17, 19, 24, 0.02);
}

.row-left {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.row-label {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text);
}

.segmented {
  display: inline-flex;
  padding: 3px;
  border-radius: 999px;
  background: rgba(17, 19, 24, 0.05);
}

.segmented button {
  border: none;
  background: transparent;
  color: var(--text-2);
  font-family: inherit;
  font-size: 0.9rem;
  padding: 0.4rem 1rem;
  border-radius: 999px;
  cursor: pointer;
  transition:
    transform 0.3s var(--spring-soft),
    background 0.2s var(--ease),
    color 0.2s var(--ease),
    box-shadow 0.2s var(--ease);
}

.segmented button:hover {
  transform: scale(1.02);
}

.segmented button.active {
  background: var(--grad-main);
  color: #fff;
  font-weight: 600;
  box-shadow: var(--shadow-blue);
}

.about {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
  padding-top: 1rem;
}

.about-title {
  margin: 0 0 0.4rem;
  font-size: 1.15rem;
  font-weight: 700;
}

.about-row {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  font-size: 0.95rem;
  padding-bottom: 0.7rem;
  border-bottom: 1px solid var(--border);
}

.about-k {
  color: var(--text-3);
}

.about-v {
  color: var(--text);
  font-weight: 600;
}

.about .btn {
  align-self: flex-start;
  margin-top: 0.5rem;
}

@media (max-width: 640px) {
  .settings {
    padding: 3rem 1.4rem 4rem;
    gap: 2rem;
  }
  .row {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }
  .segmented {
    width: 100%;
  }
  .segmented button {
    flex: 1;
    padding: 0.6rem 0.5rem;
  }
}
</style>
