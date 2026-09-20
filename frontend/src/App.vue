<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { t } from './i18n/useLanguage'
import { applyMotion } from './settings'

const scrolled = ref(false)

function onScroll() {
  scrolled.value = window.scrollY > 6
}

onMounted(() => {
  applyMotion()
  onScroll()
  window.addEventListener('scroll', onScroll, { passive: true })
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', onScroll)
})
</script>

<template>
  <div class="app-shell">
    <nav class="topnav" :class="{ scrolled }">
      <router-link class="brand" to="/">PrintMind</router-link>

      <div class="nav-right">
        <div class="nav-links">
          <router-link to="/">{{ t('nav.home') }}</router-link>
          <router-link to="/diagnose">{{ t('nav.diagnose') }}</router-link>
          <router-link to="/experiment-summary">{{ t('nav.experiments') }}</router-link>
          <router-link to="/history">{{ t('nav.history') }}</router-link>
          <router-link to="/tribute">{{ t('nav.tribute') }}</router-link>
        </div>

        <router-link class="settings-link" to="/settings" :title="t('nav.settings')">
          <span class="gear" aria-hidden="true">⚙</span>
          <span class="settings-text">{{ t('nav.settings') }}</span>
        </router-link>
      </div>
    </nav>

    <router-view v-slot="{ Component }">
      <transition name="page" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
}

.topnav {
  height: 68px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0 2rem;
  position: sticky;
  top: 0;
  z-index: 30;
  background: rgba(247, 248, 250, 0.72);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-bottom: 1px solid transparent;
  transition:
    background 0.24s var(--ease),
    border-color 0.24s var(--ease),
    backdrop-filter 0.24s var(--ease);
}

.topnav.scrolled {
  background: rgba(247, 248, 250, 0.84);
  backdrop-filter: blur(16px) saturate(1.2);
  -webkit-backdrop-filter: blur(16px) saturate(1.2);
  border-bottom-color: var(--border);
}

.brand {
  font-weight: 700;
  font-size: 1.06rem;
  color: var(--text);
  text-decoration: none;
  letter-spacing: -0.01em;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.nav-links {
  display: flex;
  gap: 0.3rem;
  font-size: 0.94rem;
}

.nav-links a {
  color: var(--text-2);
  text-decoration: none;
  padding: 0.34rem 0.72rem;
  border-radius: 999px;
  border: 1px solid transparent;
  transition:
    color 0.18s var(--ease),
    background 0.18s var(--ease),
    border-color 0.18s var(--ease);
}

.nav-links a:hover {
  color: var(--text-main);
  background: rgba(16, 18, 24, 0.045);
}

.nav-links a.router-link-active {
  color: var(--blue-bright);
  font-weight: 700;
  background: linear-gradient(135deg, rgba(47, 128, 255, 0.14), rgba(155, 92, 255, 0.16));
  border-color: rgba(99, 102, 255, 0.24);
  box-shadow: 0 4px 12px rgba(99, 102, 255, 0.12);
}

.settings-link {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.34rem 0.75rem;
  border: 1px solid var(--border);
  border-radius: 999px;
  color: var(--text-2);
  text-decoration: none;
  font-size: 0.88rem;
  background: #fff;
  transition:
    transform 0.3s var(--spring-soft),
    color 0.18s var(--ease),
    border-color 0.18s var(--ease),
    background 0.18s var(--ease);
}

.settings-link:hover {
  color: var(--text);
  border-color: #cfd4dd;
}

.settings-link:hover .gear {
  transform: rotate(8deg) scale(1.08);
}

.settings-link:active {
  transform: scale(0.94);
}

.settings-link.router-link-active {
  color: var(--accent-strong);
  border-color: rgba(59, 130, 246, 0.4);
  background: var(--accent-soft);
}

.gear {
  font-size: 0.95rem;
  line-height: 1;
  display: inline-block;
  transition: transform 0.3s var(--spring-soft);
}

@media (max-width: 820px) {
  .topnav {
    height: auto;
    flex-wrap: wrap;
    padding: 0.7rem 1.1rem;
    gap: 0.5rem;
  }
  .nav-right {
    flex-wrap: wrap;
    gap: 0.5rem;
  }
  .nav-links {
    flex-wrap: wrap;
    font-size: 0.88rem;
  }
  .nav-links a {
    padding: 0.35rem 0.55rem;
  }
  .settings-text {
    display: none;
  }
  .settings-link {
    padding: 0.4rem 0.6rem;
  }
}
</style>
