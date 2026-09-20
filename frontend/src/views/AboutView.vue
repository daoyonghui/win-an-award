<script setup>
import { t } from '../i18n/useLanguage'
</script>

<template>
  <main class="about">
    <div class="inner">
      <h1 class="about-title">{{ t('about.title') }}</h1>
      <p class="about-intro">{{ t('about.intro') }}</p>

      <div class="rule"></div>

      <h2 class="ack-title">{{ t('about.ack.title') }}</h2>
      <div class="ack">
        <p>{{ t('about.ack.p1') }}</p>
        <p>{{ t('about.ack.p2') }}</p>
        <p>{{ t('about.ack.p3') }}</p>
        <p>{{ t('about.ack.p4') }}</p>
        <p>{{ t('about.ack.p5') }}</p>
      </div>

      <p class="signature">{{ t('about.signature') }}</p>
    </div>
  </main>
</template>

<style scoped>
.about {
  min-height: calc(100vh - 68px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
}

.inner {
  max-width: 640px;
  text-align: center;
}

.about-title {
  margin: 0;
  font-size: clamp(38px, 6vw, 64px);
  letter-spacing: -0.03em;
  font-weight: 700;
}

.about-intro {
  margin: 1rem 0 0;
  font-size: clamp(16px, 1.7vw, 20px);
  color: var(--text-2);
  line-height: 1.7;
}

.rule {
  width: 48px;
  height: 1px;
  background: var(--border-strong);
  margin: 3rem auto;
}

.ack-title {
  margin: 0 0 1.5rem;
  font-size: 0.82rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--text-3);
  font-weight: 600;
}

.ack {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.ack p {
  margin: 0;
  color: var(--text-2);
  line-height: 1.9;
}

.signature {
  margin: 3.5rem 0 0;
  font-size: 0.85rem;
  color: var(--text-3);
  letter-spacing: 0.04em;
}
</style>
