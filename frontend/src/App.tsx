import {
  Badge,
  Body1,
  Button,
  Card,
  CardHeader,
  Field,
  FluentProvider,
  Input,
  MessageBar,
  MessageBarBody,
  Spinner,
  Subtitle1,
  Text,
  Title1,
  webLightTheme,
} from '@fluentui/react-components'
import {
  CalendarLtr24Regular,
  Food24Regular,
  Search24Regular,
} from '@fluentui/react-icons'
import { useMemo, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import './App.css'
import {
  ApiClientError,
  getMeals,
  searchSchools,
} from './api/client'
import type {
  Meal,
  School,
} from './api/client'

type AsyncState = 'idle' | 'loading' | 'success' | 'empty' | 'error'

const MAX_RANGE_DAYS = 31

function App() {
  const [schoolQuery, setSchoolQuery] = useState('')
  const [schoolSearchState, setSchoolSearchState] = useState<AsyncState>('idle')
  const [schoolResults, setSchoolResults] = useState<School[]>([])
  const [selectedSchool, setSelectedSchool] = useState<School | null>(null)
  const [hasMoreSchools, setHasMoreSchools] = useState(false)
  const [schoolMessage, setSchoolMessage] = useState('')
  const [fromDate, setFromDate] = useState('')
  const [toDate, setToDate] = useState('')
  const [mealQueryState, setMealQueryState] = useState<AsyncState>('idle')
  const [mealResults, setMealResults] = useState<Meal[]>([])
  const [mealMessage, setMealMessage] = useState('')
  const [mealResultStale, setMealResultStale] = useState(false)
  const schoolRequestRef = useRef(0)
  const mealRequestRef = useRef(0)
  const mealResultSectionRef = useRef<HTMLDivElement | null>(null)

  const dateRangeError = useMemo(() => validateDateRange(fromDate, toDate), [fromDate, toDate])
  const canSearch = schoolQuery.trim().length > 0 && schoolSearchState !== 'loading'
  const canLoadMeals =
    selectedSchool !== null &&
    fromDate !== '' &&
    toDate !== '' &&
    dateRangeError === '' &&
    mealQueryState !== 'loading'

  function scrollToMealResults() {
    window.setTimeout(() => {
      if (typeof mealResultSectionRef.current?.scrollIntoView === 'function') {
        mealResultSectionRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
    }, 0)
  }

  async function handleSchoolSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const query = schoolQuery.trim()
    if (!query) {
      setSchoolSearchState('idle')
      setSchoolMessage('학교명을 입력해 주세요.')
      setSchoolResults([])
      setHasMoreSchools(false)
      return
    }

    const requestId = schoolRequestRef.current + 1
    schoolRequestRef.current = requestId
    setSchoolSearchState('loading')
    setSchoolMessage('')
    setSelectedSchool(null)
    setMealResults([])
    setMealResultStale(false)
    setMealQueryState('idle')

    try {
      const result = await searchSchools(query)
      if (schoolRequestRef.current !== requestId) return
      setSchoolResults(result.schools)
      setHasMoreSchools(result.hasMore)
      setSchoolSearchState(result.schools.length > 0 ? 'success' : 'empty')
      setSchoolMessage(
        result.schools.length === 0
          ? '검색 결과가 없습니다. 다른 학교명을 입력해 보세요.'
          : result.hasMore
            ? '검색 결과가 20개를 초과해 일부만 표시합니다. 더 구체적인 학교명을 입력해 주세요.'
            : '',
      )
    } catch (error) {
      if (schoolRequestRef.current !== requestId) return
      setSchoolSearchState('error')
      setSchoolResults([])
      setHasMoreSchools(false)
      setSchoolMessage(getErrorMessage(error, '학교 검색에 실패했습니다. 다시 시도해 주세요.'))
    }
  }

  async function handleMealSearch() {
    if (!selectedSchool) {
      setMealMessage('먼저 학교를 선택해 주세요.')
      return
    }
    const validationMessage = validateDateRange(fromDate, toDate)
    if (validationMessage) {
      setMealMessage(validationMessage)
      return
    }

    const requestId = mealRequestRef.current + 1
    mealRequestRef.current = requestId
    setMealQueryState('loading')
    setMealMessage('')
    setMealResultStale(false)

    try {
      const result = await getMeals(selectedSchool, fromDate, toDate)
      if (mealRequestRef.current !== requestId) return
      setMealResults(result.meals)
      setMealQueryState(result.meals.length > 0 ? 'success' : 'empty')
      setMealMessage(
        result.meals.length === 0
          ? `${selectedSchool.name}의 ${fromDate} ~ ${toDate} 기간에는 NEIS에 등록된 중식 정보가 없습니다. 방학, 공휴일, 주말 또는 아직 식단이 등록되지 않은 날짜일 수 있습니다.`
          : `${selectedSchool.name}의 ${fromDate} ~ ${toDate} 중식 ${result.meals.length}건을 조회했습니다.`,
      )
      scrollToMealResults()
    } catch (error) {
      if (mealRequestRef.current !== requestId) return
      setMealQueryState('error')
      setMealResults([])
      setMealMessage(getErrorMessage(error, '급식 조회에 실패했습니다. 다시 시도해 주세요.'))
      scrollToMealResults()
    }
  }

  function handleSelectSchool(school: School) {
    setSelectedSchool(school)
    setMealResults([])
    setMealQueryState('idle')
    setMealMessage('')
    setMealResultStale(false)
  }

  function handleDateChange(kind: 'from' | 'to', value: string) {
    if (kind === 'from') {
      setFromDate(value)
    } else {
      setToDate(value)
    }
    if (mealResults.length > 0) {
      setMealResultStale(true)
    }
  }

  return (
    <FluentProvider theme={webLightTheme}>
      <main className="app-shell">
        <section className="hero-section">
          <Badge appearance="tint" color="brand">NEIS 중식 조회</Badge>
          <Title1 as="h1">급식 배틀</Title1>
          <Body1>
            학교 이름 일부만 입력하고 날짜 범위를 선택하면 선택한 학교의 중식 메뉴를
            날짜별로 확인할 수 있습니다.
          </Body1>
        </section>

        <section className="flow-grid" aria-label="급식 조회 단계">
          <Card className="flow-card">
            <CardHeader
              image={<Search24Regular />}
              header={<Subtitle1>1. 학교 검색 및 선택</Subtitle1>}
              description="학교명, 지역, 교육청, 학교 종류를 확인하고 한 학교를 선택하세요."
            />
            <form className="search-row" onSubmit={handleSchoolSearch}>
              <Field label="학교명" validationMessage={schoolMessage || undefined}>
                <Input
                  value={schoolQuery}
                  onChange={(_, data) => setSchoolQuery(data.value)}
                  placeholder="예: 서울"
                  contentBefore={<Search24Regular />}
                />
              </Field>
              <Button appearance="primary" type="submit" disabled={!canSearch}>
                검색
              </Button>
            </form>

            {schoolSearchState === 'loading' && <Spinner label="학교를 검색하는 중입니다." />}
            {hasMoreSchools && schoolSearchState === 'success' && (
              <MessageBar intent="warning">
                <MessageBarBody>검색 결과가 일부만 표시됩니다. 더 구체적으로 입력해 주세요.</MessageBarBody>
              </MessageBar>
            )}
            <div className="result-list" aria-live="polite">
              {schoolResults.map((school) => (
                <button
                  className={`school-option ${
                    selectedSchool?.officeCode === school.officeCode &&
                    selectedSchool?.schoolCode === school.schoolCode
                      ? 'selected'
                      : ''
                  }`}
                  key={`${school.officeCode}-${school.schoolCode}`}
                  onClick={() => handleSelectSchool(school)}
                  type="button"
                >
                  <strong>{school.name}</strong>
                  <span>{school.regionName} · {school.officeName} · {school.schoolType}</span>
                </button>
              ))}
            </div>
          </Card>

          <Card className="flow-card">
            <CardHeader
              image={<CalendarLtr24Regular />}
              header={<Subtitle1>2. 날짜 범위 선택</Subtitle1>}
              description="시작일과 종료일을 포함해 최대 31일까지 조회할 수 있습니다."
            />
            <div className="date-grid">
              <Field label="시작일">
                <Input
                  type="date"
                  value={fromDate}
                  onChange={(_, data) => handleDateChange('from', data.value)}
                />
              </Field>
              <Field label="종료일" validationMessage={dateRangeError || undefined}>
                <Input
                  type="date"
                  value={toDate}
                  onChange={(_, data) => handleDateChange('to', data.value)}
                />
              </Field>
            </div>
            {selectedSchool ? (
              <MessageBar intent="success">
                <MessageBarBody>
                  선택된 학교: {selectedSchool.name} ({selectedSchool.regionName})
                </MessageBarBody>
              </MessageBar>
            ) : (
              <MessageBar>
                <MessageBarBody>급식 조회를 위해 먼저 학교를 선택해 주세요.</MessageBarBody>
              </MessageBar>
            )}
            {mealResultStale && (
              <MessageBar intent="warning">
                <MessageBarBody>날짜 조건이 변경되었습니다. 새 조건으로 다시 조회해 주세요.</MessageBarBody>
              </MessageBar>
            )}
            <Button appearance="primary" disabled={!canLoadMeals} onClick={handleMealSearch}>
              중식 조회
            </Button>
          </Card>
        </section>

        <div ref={mealResultSectionRef} />
        <Card className="result-card">
          <CardHeader
            image={<Food24Regular />}
            header={<Subtitle1>3. 날짜별 중식 결과</Subtitle1>}
            description="NEIS가 제공한 메뉴, 열량, 영양정보, 원산지, 급식인원수를 표시합니다."
          />
          <section aria-live="polite" className="meal-state">
            {mealQueryState === 'loading' && <Spinner label="중식 정보를 불러오는 중입니다." />}
            {mealMessage && (
              <MessageBar intent={mealQueryState === 'error' ? 'error' : 'info'}>
                <MessageBarBody>{mealMessage}</MessageBarBody>
              </MessageBar>
            )}
            {mealResults.length > 0 && (
              <div className="meal-grid">
                {mealResults.map((meal) => (
                  <article className="meal-card" key={meal.date}>
                    <div className="meal-header">
                      <Text weight="semibold">{formatDate(meal.date)}</Text>
                      <Badge color="success">{meal.mealType}</Badge>
                    </div>
                    <ul className="dish-list">
                      {meal.dishes.map((dish) => <li key={dish}>{dish}</li>)}
                    </ul>
                    <dl className="meal-details">
                      <Detail label="열량" value={meal.calories} />
                      <Detail label="영양정보" value={meal.nutrition} multiline />
                      <Detail label="원산지" value={meal.origin} multiline />
                      <Detail label="급식인원수" value={meal.servings?.toLocaleString('ko-KR')} />
                    </dl>
                  </article>
                ))}
              </div>
            )}
          </section>
        </Card>
      </main>
    </FluentProvider>
  )
}

function Detail({ label, value, multiline = false }: { label: string; value?: string | null; multiline?: boolean }) {
  return (
    <>
      <dt>{label}</dt>
      <dd className={multiline ? 'multiline' : undefined}>{value || '제공되지 않음'}</dd>
    </>
  )
}

function validateDateRange(fromDate: string, toDate: string): string {
  if (!fromDate || !toDate) return ''
  const from = new Date(`${fromDate}T00:00:00`)
  const to = new Date(`${toDate}T00:00:00`)
  if (Number.isNaN(from.getTime()) || Number.isNaN(to.getTime())) {
    return '올바른 날짜를 입력해 주세요.'
  }

  if (from > to) {
    return '시작일은 종료일보다 늦을 수 없습니다.'
  }
  const days = Math.floor((to.getTime() - from.getTime()) / 86_400_000) + 1
  if (days > MAX_RANGE_DAYS) {
    return '조회 기간은 최대 31일까지 가능합니다.'
  }
  return ''
}

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof ApiClientError) {
    return `${error.apiError.message} (요청 ID: ${error.apiError.requestId})`
  }
  return fallback
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat('ko-KR', {
    dateStyle: 'full',
  }).format(new Date(`${value}T00:00:00`))
}

export default App
