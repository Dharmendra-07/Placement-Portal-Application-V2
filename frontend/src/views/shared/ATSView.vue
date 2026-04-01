<template>
  <div class="container py-4" style="max-width:880px">
    <div class="d-flex align-items-center gap-3 mb-4">
      <div>
        <h5 class="fw-bold mb-0">ATS Resume Screener</h5>
        <p class="text-muted small mb-0">
          Check how well a resume matches a job description
        </p>
      </div>
      <span class="badge bg-primary ms-auto">AI-powered</span>
    </div>

    <!-- Mode selector (students get both; companies can use drive ID) -->
    <div class="card border-0 shadow-sm mb-4">
      <div class="card-header bg-white fw-semibold">Input Mode</div>
      <div class="card-body">
        <div class="d-flex gap-2 flex-wrap mb-3">
          <button v-for="m in modes" :key="m.value"
                  class="btn btn-sm"
                  :class="mode === m.value ? 'btn-primary' : 'btn-outline-secondary'"
                  @click="mode = m.value; resetResult()">
            {{ m.label }}
          </button>
        </div>

        <!-- Manual text mode -->
        <div v-if="mode === 'manual'" class="row g-3">
          <div class="col-md-6">
            <label class="form-label fw-medium">Job Description *</label>
            <textarea v-model="form.jd_text" class="form-control" rows="8"
                      placeholder="Paste the job description here...
Include: job title, required skills, experience, responsibilities."></textarea>
          </div>
          <div class="col-md-6">
            <label class="form-label fw-medium">Resume Text *</label>
            <textarea v-model="form.resume_text" class="form-control" rows="8"
                      placeholder="Paste your resume text here...
Include: skills, experience, education, projects."></textarea>
          </div>
        </div>

        <!-- Drive picker mode (company or student) -->
        <div v-else-if="mode === 'drive'" class="row g-3">
          <div class="col-md-6">
            <label class="form-label fw-medium">Select Drive</label>
            <select v-model="form.drive_id" class="form-select">
              <option value="">Choose a placement drive...</option>
              <option v-for="d in drives" :key="d.id" :value="d.id">
                {{ d.job_title }} — {{ d.company_name }}
              </option>
            </select>
          </div>
          <div class="col-md-6">
            <label class="form-label fw-medium">Resume Text</label>
            <textarea v-model="form.resume_text" class="form-control" rows="5"
                      placeholder="Leave blank to use your profile skills, or paste resume text..."></textarea>
          </div>
        </div>

        <div v-if="errorMsg" class="alert alert-danger py-2 small mt-3">
          {{ errorMsg }}
        </div>

        <button class="btn btn-primary mt-3"
                :disabled="screening"
                @click="runScreen">
          <span v-if="screening"
                class="spinner-border spinner-border-sm me-1"></span>
          {{ screening ? 'Analysing…' : 'Run ATS Screen' }}
        </button>
      </div>
    </div>

    <!-- ── Result ── -->
    <div v-if="result" class="card border-0 shadow-sm">
      <div class="card-header bg-white d-flex align-items-center
                  justify-content-between fw-semibold">
        Screening Result
        <button class="btn btn-sm btn-outline-secondary" @click="resetResult">
          Clear
        </button>
      </div>
      <div class="card-body">

        <!-- Score header -->
        <div class="row align-items-center g-3 mb-4">
          <div class="col-auto">
            <div class="d-flex align-items-center justify-content-center rounded-3 fw-bold"
                 :style="`width:80px;height:80px;font-size:2rem;
                          background:${result.grade_color}20;
                          color:${result.grade_color};
                          border:3px solid ${result.grade_color}`">
              {{ result.grade }}
            </div>
          </div>
          <div class="col">
            <h4 class="fw-bold mb-1">{{ result.score }}% Match</h4>
            <p class="text-muted mb-2">{{ result.grade_label }}</p>
            <div class="progress" style="height:10px;max-width:400px">
              <div class="progress-bar"
                   :style="`width:${result.score}%;
                            background:${result.grade_color}`"></div>
            </div>
          </div>
          <div class="col-md-3 text-md-end">
            <div class="text-muted small">
              <div>JD skills: {{ result.jd_skill_count }}</div>
              <div>Resume skills: {{ result.resume_skill_count }}</div>
              <div>Words: {{ result.word_count }}</div>
            </div>
          </div>
        </div>

        <!-- Skills grid -->
        <div class="row g-3 mb-4">
          <div class="col-md-6">
            <div class="card bg-success bg-opacity-10 border-0">
              <div class="card-body">
                <h6 class="fw-semibold text-success mb-2">
                  ✓ Matched Skills ({{ result.matched_skills.length }})
                </h6>
                <div class="d-flex flex-wrap gap-1">
                  <span v-for="sk in result.matched_skills" :key="sk"
                        class="badge bg-success text-capitalize">{{ sk }}</span>
                  <span v-if="!result.matched_skills.length"
                        class="text-muted small">None matched</span>
                </div>
              </div>
            </div>
          </div>
          <div class="col-md-6">
            <div class="card bg-danger bg-opacity-10 border-0">
              <div class="card-body">
                <h6 class="fw-semibold text-danger mb-2">
                  ✗ Missing Skills ({{ result.missing_skills.length }})
                </h6>
                <div class="d-flex flex-wrap gap-1">
                  <span v-for="sk in result.missing_skills" :key="sk"
                        class="badge bg-danger text-capitalize">{{ sk }}</span>
                  <span v-if="!result.missing_skills.length"
                        class="text-muted small">None missing!</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Match breakdown bar -->
        <div class="mb-4">
          <p class="fw-medium small mb-1">Match breakdown</p>
          <div class="progress" style="height:20px;border-radius:10px">
            <div class="progress-bar bg-success"
                 :style="`width:${result.match_breakdown.matched /
                   (result.match_breakdown.matched + result.match_breakdown.missing || 1) * 100}%`">
              {{ result.match_breakdown.matched }} matched
            </div>
            <div class="progress-bar bg-danger"
                 :style="`width:${result.match_breakdown.missing /
                   (result.match_breakdown.matched + result.match_breakdown.missing || 1) * 100}%`">
              {{ result.match_breakdown.missing }} missing
            </div>
          </div>
        </div>

        <!-- Common keywords -->
        <div v-if="result.common_keywords.length" class="mb-4">
          <p class="fw-medium small mb-2">Common keywords found in both</p>
          <div class="d-flex flex-wrap gap-1">
            <span v-for="kw in result.common_keywords" :key="kw"
                  class="badge bg-light text-secondary border text-capitalize">
              {{ kw }}
            </span>
          </div>
        </div>

        <!-- Resume note -->
        <div class="alert py-2 mb-3"
             :class="result.word_count < 150 || result.word_count > 1200
               ? 'alert-warning' : 'alert-info'">
          <i class="bi bi-info-circle me-2"></i>
          {{ result.length_note }}
        </div>

        <!-- Suggestions -->
        <div v-if="result.suggestions.length">
          <h6 class="fw-semibold mb-3">Improvement Suggestions</h6>
          <div class="row g-2">
            <div class="col-md-6" v-for="s in result.suggestions" :key="s.skill">
              <div class="card border-0 bg-light h-100">
                <div class="card-body py-2 px-3">
                  <div class="fw-medium small text-capitalize text-danger mb-1">
                    {{ s.skill }}
                  </div>
                  <div class="text-muted" style="font-size:.8rem">{{ s.tip }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script>
import api from '../../api'
import { mapGetters } from 'vuex'

export default {
  name: 'ATSView',
  data() {
    return {
      mode:      'manual',
      form:      { jd_text: '', resume_text: '', drive_id: '' },
      drives:    [],
      result:    null,
      screening: false,
      errorMsg:  '',
      modes: [
        { value: 'manual', label: 'Paste text'  },
        { value: 'drive',  label: 'Use a drive' },
      ],
    }
  },
  computed: {
    ...mapGetters(['isStudent', 'isCompany']),
  },
  async created() {
    // Pre-load approved drives for the drive picker
    try {
      const endpoint = this.isCompany ? '/company/drives' : '/student/drives'
      const { data } = await api.get(endpoint)
      this.drives = Array.isArray(data) ? data : (data.drives || [])
    } catch { /* silent */ }
  },
  methods: {
    resetResult() {
      this.result   = null
      this.errorMsg = ''
    },
    async runScreen() {
      this.errorMsg = ''
      this.result   = null

      const payload = {}
      if (this.mode === 'manual') {
        if (!this.form.jd_text.trim()) {
          this.errorMsg = 'Please enter the job description.'
          return
        }
        if (!this.form.resume_text.trim()) {
          this.errorMsg = 'Please enter the resume text.'
          return
        }
        payload.jd_text     = this.form.jd_text
        payload.resume_text = this.form.resume_text
      } else {
        if (!this.form.drive_id) {
          this.errorMsg = 'Please select a drive.'
          return
        }
        payload.drive_id    = this.form.drive_id
        payload.resume_text = this.form.resume_text || undefined
      }

      this.screening = true
      try {
        const { data } = await api.post('/ats/screen', payload)
        this.result = data
        this.$nextTick(() => {
          document.querySelector('.card.border-0.shadow-sm:last-of-type')
            ?.scrollIntoView({ behavior: 'smooth' })
        })
      } catch (err) {
        this.errorMsg = err.response?.data?.message || 'Screening failed.'
      } finally { this.screening = false }
    },
  },
}
</script>
