<script setup>
import { t } from '../i18n/useLanguage'
</script>

<template>
  <main class="tribute">
    <header class="head">
      <h1 class="section-title">{{ t('tribute.title') }}</h1>
      <p class="subtitle">{{ t('tribute.subtitle') }}</p>
    </header>

    <section class="copy">
      <p>{{ t('tribute.p1') }}</p>
      <p>{{ t('tribute.p2') }}</p>
      <p>{{ t('tribute.p3') }}</p>
      <p>{{ t('tribute.p4') }}</p>
      <p>{{ t('tribute.p5') }}</p>
      <p>{{ t('tribute.p6') }}</p>
      <p class="closing-line">{{ t('tribute.p7') }}</p>
    </section>

    <section class="people">
      <!-- 核心人物 -->
      <article class="person primary">
        <span class="label">{{ t('tribute.card1.label') }}</span>
        <h2 class="name">{{ t('tribute.card1.name') }}</h2>
        <div class="roles">
          <span class="role">{{ t('tribute.card1.role1') }}</span>
          <span class="role">{{ t('tribute.card1.role2') }}</span>
          <span class="role">{{ t('tribute.card1.role3') }}</span>
        </div>
        <p class="desc">{{ t('tribute.card1.desc') }}</p>
        <p class="desc">{{ t('tribute.card1.desc2') }}</p>
      </article>

      <!-- 协作者 -->
      <article class="person secondary">
        <h2 class="name">{{ t('tribute.card2.name') }}</h2>
        <div class="roles">
          <span class="role">{{ t('tribute.card2.role1') }}</span>
          <span class="role">{{ t('tribute.card2.role2') }}</span>
        </div>
        <p class="desc">{{ t('tribute.card2.desc') }}</p>
      </article>
    </section>

    <footer class="foot">
      <p class="closing">{{ t('tribute.closing') }}</p>
      <p class="signature">{{ t('tribute.signature') }}</p>
    </footer>
  </main>
</template>

<style scoped>
.tribute {
  max-width: 1050px;
  margin: 0 auto;
  padding: 5rem 2rem 6rem;
  display: flex;
  flex-direction: column;
  gap: 4rem;
}

.head {
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.subtitle {
  margin: 0 auto;
  max-width: 44rem;
  font-size: clamp(16px, 1.7vw, 20px);
  color: var(--text-2);
  line-height: 1.7;
}

.copy {
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
  max-width: 46rem;
  margin: 0 auto;
}

.copy p {
  margin: 0;
  color: var(--text-2);
  line-height: 1.95;
  font-size: 1.02rem;
}

.closing-line {
  color: var(--text) !important;
  font-weight: 600;
}

.people {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.person {
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  background: var(--surface);
  padding: 2.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.person.primary {
  background: linear-gradient(180deg, #fbfbff, #f5f6fc);
  border-color: rgba(139, 92, 246, 0.3);
  box-shadow: var(--shadow-md);
  padding: 3rem;
}

.person.secondary {
  max-width: 46rem;
  align-self: flex-end;
  padding: 1.75rem 2rem;
  background: var(--surface-2);
}

.label {
  align-self: flex-start;
  font-size: 0.72rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  font-weight: 700;
  color: #fff;
  background: var(--grad-main);
  border: none;
  border-radius: 999px;
  padding: 0.22rem 0.75rem;
  box-shadow: var(--shadow-purple);
}

.name {
  margin: 0;
  font-size: clamp(28px, 3.4vw, 40px);
  letter-spacing: -0.02em;
  font-weight: 700;
}

.person.secondary .name {
  font-size: clamp(20px, 2.2vw, 26px);
}

.roles {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.role {
  font-size: 0.85rem;
  color: var(--text-2);
  background: rgba(17, 19, 24, 0.04);
  border-radius: 8px;
  padding: 0.25rem 0.6rem;
}

.person.primary .role {
  color: var(--accent-strong);
  background: var(--accent-soft);
}

.desc {
  margin: 0;
  color: var(--text-2);
  line-height: 1.9;
}

.person.primary .desc {
  max-width: 46rem;
}

.foot {
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 2rem;
  margin-top: 1rem;
}

.closing {
  margin: 0 auto;
  max-width: 40rem;
  color: var(--text-2);
  line-height: 2;
}

.signature {
  margin: 0;
  font-size: 0.85rem;
  letter-spacing: 0.04em;
  background: var(--grad-main);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  font-weight: 600;
}

@media (max-width: 760px) {
  .tribute {
    gap: 3rem;
    padding: 3.5rem 1.4rem 4rem;
  }
  .person,
  .person.primary {
    padding: 1.75rem;
  }
  .person.secondary {
    align-self: stretch;
    max-width: none;
  }
}
</style>
