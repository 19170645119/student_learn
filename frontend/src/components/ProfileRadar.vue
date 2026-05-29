<template>
  <div class="radar-wrap" :style="{ width: size + 'px', height: size + 'px' }">
    <svg :width="size" :height="size" :viewBox="'0 0 ' + size + ' ' + size">
      <!-- Background grid -->
      <polygon v-for="level in 5" :key="level"
        :points="gridPoints(level / 5)"
        :fill="level === 5 ? 'rgba(91,127,255,0.04)' : 'none'"
        :stroke="level === 5 ? 'rgba(91,127,255,0.2)' : 'rgba(255,255,255,0.05)'"
        stroke-width="1"
      />
      <!-- Axis lines -->
      <line v-for="(d, i) in dimensions" :key="'axis-' + i"
        :x1="cx" :y1="cy"
        :x2="axisPoints[i].x" :y2="axisPoints[i].y"
        stroke="rgba(255,255,255,0.08)" stroke-width="1"
      />
      <!-- Data area -->
      <polygon v-if="hasAnyData"
        :points="dataPointsStr"
        fill="rgba(91,127,255,0.15)"
        stroke="rgba(91,127,255,0.5)"
        stroke-width="2"
      />
      <!-- Data dots -->
      <circle v-for="(d, i) in dimensions" :key="'dot-' + i"
        :cx="dataPoints[i].x" :cy="dataPoints[i].y" r="4"
        :fill="scoreVal(d) > 1 ? '#5B7FFF' : 'rgba(255,255,255,0.15)'"
        :stroke="scoreVal(d) > 1 ? '#a78bfa' : 'rgba(255,255,255,0.1)'"
        stroke-width="1.5"
      />
      <!-- Labels -->
      <text v-for="(d, i) in dimensions" :key="'label-' + i"
        :x="labelPoints[i].x" :y="labelPoints[i].y"
        :text-anchor="labelAnchors[i]"
        :dominant-baseline="labelBaselines[i]"
        class="radar-label"
      >{{ d.label }}</text>
    </svg>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  dimensions: { type: Array, default: () => [] },
  size: { type: Number, default: 260 }
})

const cx = computed(() => props.size / 2)
const cy = computed(() => props.size / 2)
const radius = computed(() => props.size * 0.34)

const axisPoints = computed(() => {
  return props.dimensions.map((_, i) => {
    const angle = (Math.PI * 2 * i) / props.dimensions.length - Math.PI / 2
    return { x: cx.value + radius.value * Math.cos(angle), y: cy.value + radius.value * Math.sin(angle) }
  })
})

const labelPoints = computed(() => {
  return props.dimensions.map((_, i) => {
    const angle = (Math.PI * 2 * i) / props.dimensions.length - Math.PI / 2
    const r = radius.value * 1.35
    return { x: cx.value + r * Math.cos(angle), y: cy.value + r * Math.sin(angle) }
  })
})

const labelAnchors = computed(() => {
  return props.dimensions.map((_, i) => {
    const angle = (Math.PI * 2 * i) / props.dimensions.length - Math.PI / 2
    const x = Math.cos(angle)
    if (Math.abs(x) < 0.1) return 'middle'
    return x > 0 ? 'start' : 'end'
  })
})

const labelBaselines = computed(() => {
  return props.dimensions.map((_, i) => {
    const angle = (Math.PI * 2 * i) / props.dimensions.length - Math.PI / 2
    const y = Math.sin(angle)
    if (Math.abs(y) < 0.1) return 'middle'
    return y > 0 ? 'hanging' : 'baseline'
  })
})

function scoreVal(dim) {
  const v = (dim.value || '').trim()
  if (!v || v === '待完善') return 1
  const items = v.split(/[、，,+&\/]/).filter(s => s.trim())
  const itemCount = items.length
  const detailBonus = v.length > 20 ? 1 : 0
  return Math.min(1 + itemCount * 2 + detailBonus, 10)
}
const hasAnyData = computed(() => props.dimensions.some(d => scoreVal(d) > 1))

const dataPoints = computed(() => {
  return props.dimensions.map((d, i) => {
    const s = scoreVal(d)
    const r = radius.value * (s / 10)
    const angle = (Math.PI * 2 * i) / props.dimensions.length - Math.PI / 2
    return { x: cx.value + r * Math.cos(angle), y: cy.value + r * Math.sin(angle) }
  })
})

const dataPointsStr = computed(() => dataPoints.value.map(p => p.x + ',' + p.y).join(' '))

function gridPoints(scale) {
  const r = radius.value * scale
  return props.dimensions.map((_, i) => {
    const angle = (Math.PI * 2 * i) / props.dimensions.length - Math.PI / 2
    return (cx.value + r * Math.cos(angle)) + ',' + (cy.value + r * Math.sin(angle))
  }).join(' ')
}
</script>

<style scoped>
.radar-wrap { margin: 0 auto; }
.radar-label { font-size: 10px; fill: rgba(255,255,255,0.5); }
</style>
