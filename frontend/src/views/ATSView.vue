<template>
  <div class="container py-4" style="max-width:820px">
    <div class="d-flex align-items-center gap-2 mb-4">
      <div class="rounded-3 d-flex align-items-center justify-content-center"
           style="width:42px;height:42px;background:#0d6efd">
        <i class="bi bi-robot text-white fs-5"></i>
      </div>
      <div>
        <h5 class="fw-bold mb-0">ATS Resume Screener</h5>
        <p class="text-muted small mb-0">
          Check how well your resume matches a job description
        </p>
      </div>
    </div>

    <!-- Input form -->
    <div class="card border-0 shadow-sm mb-4" v-if="!result">
      <div class="card-body p-4">
        <div v-if="errorMsg" class="alert alert-danger py-2 small">{{ errorMsg }}</div>

        <div class="mb-3">
          <label class="form-label fw-medium">Resume Text <span class="text-danger">*</span></label>
          <textarea v-model="form.resume_text" class="form-control" rows="8"
                    placeholder="Paste your resume text here (copy-paste from PDF/Word)..."></textarea>
          <div class="text-muted" style="font-size:11px;margin-top:3px">
            {{ wordCount }} words · minimum 150 recommended
          </div>
        </div>

        <div class="mb-3">
          <label class="form-label fw-medium">Job Description</label>
          <textarea v-model="form.job_description" class="form-control" rows="5"
                    placeholder="Paste the job description here (optional but improves accuracy)..."></textarea>
        </div>

        <div class="row g-3">
          <div class="col-md-8">
            <label class="form-label fw-medium">
              Required Skills
              <span class="text-muted small">(comma-separated, optional)</span>
            </label>
            <input v-model="form.required_skills" type="text" class="form-control"
                   placeholder="Python, React, SQL, Docker" />
          </div>
          <div class="col-md-4">
            <label class="form-label fw-medium">Min CGPA required</label>
            <input v-model.number="form.min_cgpa" type="number"
                   class="form-control" step="0.1" min="0" max="10"
                   placeholder="e.g. 7.0" />
          </div>
        </div>

        <button class="btn btn-primary mt-4 px-4"
                :disabled="loading || !form.resume_text.trim()"
                @click="screen">
          <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
          {{ loading ? 'Analysing…' : 'Screen Resume' }}
        </button>
      </div>
    </div>

    <!-- Results -->
    <div v-if="result">

      <!-- Score card -->
      <div class="card border-0 shadow-sm mb-3"
           :class="`border-start border-4 border-${result.verdict_color}`">
        <div class="card-body py-3">
          <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
            <div>
              <div class="fw-bold fs-4 mb-0"
                   :class="`text-${result.verdict_color}`">
                {{ result.overall_score }}%
              </div>
              <div class="text-muted small">Overall ATS Score</div>
            </div>
            <span class="badge fs-6 fw-normal px-3 py-2"
                  :class="`bg-${result.verdict_color}`">
              {{ result.verdict }}
            </span>
            <button class="btn btn-sm btn-outline-secondary"
                    @click="result = null">
              Screen Again
            </button>
          </div>
        </div>
      </div>

      <!-- Sub-scores -->
      <div class="row g-3 mb-3">
        <div class="col-md-4" v-for="s in subScores" :key="s.label">
          <div class="card border-0 shadow-sm text-center h-100">
            <div class="card-body py-3">
              <div class="fs-3 fw-bold" :class="`text-${scoreColor(s.value)}`">
                {{ s.value }}%
              </div>
              <div class="text-muted small mt-1">{{ s.label }}</div>
              <div class="progress mt-2" style="height:4px">
                <div class="progress-bar"
                     :class="`bg-${scoreColor(s.value)}`"
                     :style="`width:${s.value}%`"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="row g-3 mb-3">
        <!-- Skill match -->
        <div class="col-md-6">
          <div class="card border-0 shadow-sm h-100">
            <div class="card-header bg-white fw-semibold">
              Skill Match
              <span class="badge bg-secondary ms-2">
                {{ result.skills.matched.length }}/{{ result.skills.required.length }}
              </span>
            </div>
            <div class="card-body">
              <div class="mb-2" v-if="result.skills.matched.length">
                <div class="text-muted small mb-1">Matched</div>
                <div class="d-flex flex-wrap gap-1">
                  <span v-for="sk in result.skills.matched" :key="sk"
                        class="badge bg-success-subtle text-success border border-success">
                    ✓ {{ sk }}
                  </span>
                </div>
              </div>
              <div v-if="result.skills.missing.length">
                <div class="text-muted small mb-1">Missing</div>
                <div class="d-flex flex-wrap gap-1">
                  <span v-for="sk in result.skills.missing" :key="sk"
                        class="badge bg-danger-subtle text-danger border border-danger">
                    ✗ {{ sk }}
                  </span>
                </div>
              </div>
              <div v-if="!result.skills.required.length" class="text-muted small">
                No specific skills provided.
              </div>
            </div>
          </div>
        </div>

        <!-- Quality checks -->
        <div class="col-md-6">
          <div class="card border-0 shadow-sm h-100">
            <div class="card-header bg-white fw-semibold">Resume Quality Checklist</div>
            <div class="card-body">
              <ul class="list-unstyled mb-0">
                <li v-for="(val, key) in result.quality_checks" :key="key"
                    class="d-flex align-items-center gap-2 py-1 border-bottom">
                  <i :class="val ? 'bi bi-check-circle-fill text-success'
                                 : 'bi bi-x-circle-fill text-danger'"></i>
                  <span class="small">{{ qualityLabel(key) }}</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <!-- CGPA -->
      <div v-if="result.cgpa.found !== null" class="card border-0 shadow-sm mb-3">
        <div class="card-body py-2 d-flex align-items-center gap-3">
          <i :class="result.cgpa.passes
              ? 'bi bi-check-circle-fill text-success fs-5'
              : 'bi bi-x-circle-fill text-danger fs-5'"></i>
          <div class="small">
            <strong>CGPA:</strong> {{ result.cgpa.found }}
            <span v-if="result.cgpa.required">
              (required: {{ result.cgpa.required }})
            </span>
          </div>
        </div>
      </div>

      <!-- JD keyword matches -->
      <div v-if="result.jd_keywords_matched?.length"
           class="card border-0 shadow-sm mb-3">
        <div class="card-header bg-white fw-semibold">JD Keyword Matches</div>
        <div class="card-body">
          <div class="d-flex flex-wrap gap-1">
            <span v-for="kw in result.jd_keywords_matched" :key="kw"
                  class="badge bg-info-subtle text-info border border-info small">
              {{ kw }}
            </span>
          </div>
        </div>
      </div>

      <!-- Improvement tips -->
      <div v-if="result.improvement_tips?.length"
           class="card border-0 shadow-sm">
        <div class="card-header bg-white fw-semibold">
          Improvement Tips
        </div>
        <ul class="list-group list-group-flush">
          <li v-for="(tip, i) in result.improvement_tips" :key="i"
              class="list-group-item d-flex gap-2 align-items-start py-2">
            <i class="bi bi-lightbulb-fill text-warning mt-1 flex-shrink-0"></i>
            <span class="small">{{ tip }}</span>
          </li>
        </ul>
      </div>

    </div>
  </div>
</template>

<script>
import api from '../api'

const QUALITY_LABELS = {
  has_email:           'Contact email present',
  has_phone:           'Phone number present',
  has_education:       'Education section present',
  has_experience:      'Experience / projects present',
  has_github:          'GitHub / GitLab profile linked',
  has_linkedin:        'LinkedIn profile linked',
  has_certifications:  'Certifications mentioned',
  adequate_length:     'Resume is adequately detailed (150+ words)',
}

export default {
  name: 'ATSView',
  data() {
    return {
      form: {
        resume_text: '', job_description: '',
        required_skills: '', min_cgpa: null,
      },
      loading:  false,
      errorMsg: '',
      result:   null,
    }
  },
  computed: {
    wordCount() {
      return this.form.resume_text.trim().split(/\s+/).filter(Boolean).length
    },
    subScores() {
      if (!this.result) return []
      return [
        { label: 'Skill Match',      value: this.result.scores.skill_match },
        { label: 'JD Keyword Match', value: this.result.scores.jd_overlap },
        { label: 'Resume Quality',   value: this.result.scores.resume_quality },
      ]
    },
  },
  methods: {
    async screen() {
      this.errorMsg = ''
      if (!this.form.resume_text.trim()) {
        this.errorMsg = 'Please paste your resume text.'
        return
      }
      this.loading = true
      try {
        const { data } = await api.post('/analytics/ats/screen', this.form)
        this.result = data
      } catch (err) {
        this.errorMsg = err.response?.data?.message || 'Screening failed.'
      } finally { this.loading = false }
    },
    scoreColor(v) {
      if (v >= 75) return 'success'
      if (v >= 50) return 'info'
      if (v >= 30) return 'warning'
      return 'danger'
    },
    qualityLabel(key) { return QUALITY_LABELS[key] || key },
  },
}
</script>
