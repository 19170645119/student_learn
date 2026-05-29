# -*- coding: utf-8 -*-
import os

content = """<template>
  <div class="vp-container" v-if="script">
    <!-- Top Control Bar -->
    <div class="vp-controls">
      <div class="vp-mode-toggle">
        <button :class="{ active: !interactiveMode }" @click="interactiveMode = false">自动播放</button>
        <button :class="{ active: interactiveMode }" @click="interactiveMode = true">交互模式</button>
      </div>
      <button class="vp-btn" @click="togglePlay" :title="playing ? '暂停' : '播放'">
        <svg v-if="!playing" width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><polygon points="5,3 19,12 5,21"/></svg>
        <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
      </button>
      <button class="vp-btn" @click="restart" title="重播">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/></svg>
      </button>
      <div class="vp-speed">
        <button v-for="s in speeds" :key="s" class="vp-speed-btn" :class="{ active: speed === s }" @click="speed = s">{{ s }}x</button>
      </div>
      <div class="vp-spacer"></div>
    </div>
  </div>
</template>
"""

print(f"Template test: {len(content)} chars ok")
