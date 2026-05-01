const RAG_EXAMPLES = [
  'What is payment success rate?',
  'How are failed payments reviewed?',
  'How are high-value clients classified?',
]

const SQL_EXAMPLES = [
  'Show total payment amount by provider.',
  'Which month had the highest number of failed payments?',
  'List the top 10 clients by total payment amount.',
]

const HYBRID_EXAMPLES = [
  'Using the KPI definition, calculate the payment success rate from the database.',
  'According to the client segmentation rules, how many high-value clients do we have?',
  'Based on the provider failure-rate threshold in the policy, which providers should be reviewed?',
]

type ExampleQuestionsProps = {
  value: string
  onSelect: (question: string) => void
}

export function ExampleQuestions({ value, onSelect }: ExampleQuestionsProps) {
  return (
    <div className="example-dropdown">
      <label htmlFor="example-question">Example questions</label>
      <select
        id="example-question"
        value={value}
        onChange={(event) => onSelect(event.target.value)}
      >
        <option value="">Choose an example...</option>
        <optgroup label="RAG">
          {RAG_EXAMPLES.map((question) => (
            <option key={question} value={question}>
              {question}
            </option>
          ))}
        </optgroup>
        <optgroup label="SQL">
          {SQL_EXAMPLES.map((question) => (
            <option key={question} value={question}>
              {question}
            </option>
          ))}
        </optgroup>
        <optgroup label="Hybrid">
          {HYBRID_EXAMPLES.map((question) => (
            <option key={question} value={question}>
              {question}
            </option>
          ))}
        </optgroup>
      </select>
    </div>
  )
}
