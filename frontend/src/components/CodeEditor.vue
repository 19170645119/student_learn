<template>
  <div class="codemirror-wrap" ref="editorRef"></div>
</template>

<script setup>
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import { EditorView, keymap, lineNumbers, highlightActiveLine } from '@codemirror/view'
import { EditorState } from '@codemirror/state'
import { defaultKeymap, indentWithTab } from '@codemirror/commands'
import { python } from '@codemirror/lang-python'
import { javascript } from '@codemirror/lang-javascript'
import { cpp } from '@codemirror/lang-cpp'
import { java } from '@codemirror/lang-java'
import { oneDark } from '@codemirror/theme-one-dark'

const props = defineProps({
  modelValue: { type: String, default: '' },
  language: { type: String, default: 'python' },
  readonly: { type: Boolean, default: false }
})

const emit = defineEmits(['update:modelValue'])
const editorRef = ref(null)
let view = null

function getLangExtension(lang) {
  const map = {
    python: python(), javascript: javascript(), js: javascript(),
    cpp: cpp(), 'c++': cpp(), java: java(),
    go: javascript(), rust: javascript(), typescript: javascript()
  }
  return map[lang] || python()
}

onMounted(() => {
  const extensions = [
    lineNumbers(),
    highlightActiveLine(),
    keymap.of([...defaultKeymap, indentWithTab]),
    getLangExtension(props.language),
    oneDark,
    EditorView.updateListener.of(update => {
      if (update.docChanged) {
        emit('update:modelValue', update.state.doc.toString())
      }
    }),
    EditorState.readOnly.of(props.readonly)
  ]

  view = new EditorView({
    state: EditorState.create({ doc: props.modelValue, extensions }),
    parent: editorRef.value
  })
})

watch(() => props.modelValue, (val) => {
  if (view && val !== view.state.doc.toString()) {
    view.dispatch({
      changes: { from: 0, to: view.state.doc.length, insert: val }
    })
  }
})

watch(() => props.readonly, (val) => {
  if (view) {
    view.dispatch({
      effects: EditorView.editable.reconfigure(EditorView.editable.of(!val))
    })
  }
})

onBeforeUnmount(() => { if (view) view.destroy() })
</script>

<style scoped>
.codemirror-wrap { border-radius: 8px; overflow: hidden; border: 1px solid var(--border); }
.codemirror-wrap :deep(.cm-editor) { font-size: 0.82rem; }
.codemirror-wrap :deep(.cm-editor.cm-focused) { outline: none; }
</style>
