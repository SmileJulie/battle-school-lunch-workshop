import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'

vi.mock('@fluentui/react-components', () => ({
  Badge: ({ children }: { children: React.ReactNode }) => <span>{children}</span>,
  Body1: ({ children }: { children: React.ReactNode }) => <p>{children}</p>,
  Button: ({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) => (
    <button {...props}>{children}</button>
  ),
  Card: ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <section className={className}>{children}</section>
  ),
  CardHeader: ({
    header,
    description,
  }: {
    header: React.ReactNode
    description?: React.ReactNode
  }) => (
    <header>
      {header}
      {description}
    </header>
  ),
  Field: ({
    children,
    label,
    validationMessage,
  }: {
    children: React.ReactElement
    label: string
    validationMessage?: string
  }) => (
    <label>
      {label}
      {children}
      {validationMessage && <span>{validationMessage}</span>}
    </label>
  ),
  FluentProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  Input: ({
    value,
    onChange,
    placeholder,
    type,
  }: {
    value: string
    onChange: (_event: React.ChangeEvent<HTMLInputElement>, data: { value: string }) => void
    placeholder?: string
    type?: string
  }) => (
    <input
      placeholder={placeholder}
      type={type}
      value={value}
      onChange={(event) => onChange(event, { value: event.currentTarget.value })}
    />
  ),
  MessageBar: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  MessageBarBody: ({ children }: { children: React.ReactNode }) => <span>{children}</span>,
  Spinner: ({ label }: { label: string }) => <span>{label}</span>,
  Subtitle1: ({ children }: { children: React.ReactNode }) => <h2>{children}</h2>,
  Text: ({ children }: { children: React.ReactNode }) => <span>{children}</span>,
  Title1: ({ children }: { children: React.ReactNode }) => <h1>{children}</h1>,
  webLightTheme: {},
}))

vi.mock('@fluentui/react-icons', () => ({
  CalendarLtr24Regular: () => null,
  Food24Regular: () => null,
  Search24Regular: () => null,
}))

const fetchMock = vi.fn()
globalThis.fetch = fetchMock

afterEach(() => {
  fetchMock.mockReset()
})

describe('App', () => {
  it('searches, selects a school, and shows lunch results', async () => {
    fetchMock
      .mockResolvedValueOnce(
        jsonResponse({
          schools: [
            {
              officeCode: 'B10',
              schoolCode: '7010057',
              name: '서울고등학교',
              officeName: '서울특별시교육청',
              regionName: '서울특별시',
              schoolType: '고등학교',
            },
          ],
          hasMore: false,
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          school: { officeCode: 'B10', schoolCode: '7010057' },
          from: '2026-08-14',
          to: '2026-08-14',
          meals: [
            {
              date: '2026-08-14',
              mealType: '중식',
              dishes: ['쌀밥', '미역국'],
              calories: '650.0 Kcal',
            },
          ],
        }),
      )

    render(<App />)
    const user = userEvent.setup()

    await user.type(screen.getByLabelText('학교명'), '서울')
    await user.click(screen.getByRole('button', { name: '검색' }))
    await user.click(await screen.findByRole('button', { name: /서울고등학교/ }))
    await user.type(screen.getByLabelText('시작일'), '2026-08-14')
    await user.type(screen.getByLabelText('종료일'), '2026-08-14')
    await user.click(screen.getByRole('button', { name: '중식 조회' }))

    expect(await screen.findByText('쌀밥')).toBeInTheDocument()
    expect(screen.getByText('미역국')).toBeInTheDocument()
    expect(fetchMock).not.toHaveBeenCalledWith(expect.stringContaining('open.neis.go.kr'), expect.anything())
  })

  it('blocks meal lookup when date range exceeds 31 days', async () => {
    render(<App />)
    const user = userEvent.setup()

    await user.type(screen.getByLabelText('시작일'), '2026-08-01')
    await user.type(screen.getByLabelText('종료일'), '2026-09-01')

    expect(screen.getByText('조회 기간은 최대 31일까지 가능합니다.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '중식 조회' })).toBeDisabled()
  })

  it('shows an explicit empty meal state when NEIS has no menu for the date', async () => {
    fetchMock
      .mockResolvedValueOnce(
        jsonResponse({
          schools: [
            {
              officeCode: 'B10',
              schoolCode: '7130101',
              name: '서울가동초등학교',
              officeName: '서울특별시교육청',
              regionName: '서울특별시',
              schoolType: '초등학교',
            },
          ],
          hasMore: false,
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          school: { officeCode: 'B10', schoolCode: '7130101' },
          from: '2026-08-14',
          to: '2026-08-14',
          meals: [],
        }),
      )

    render(<App />)
    const user = userEvent.setup()

    await user.type(screen.getByLabelText('학교명'), '서울가동')
    await user.click(screen.getByRole('button', { name: '검색' }))
    await user.click(await screen.findByRole('button', { name: /서울가동초등학교/ }))
    await user.type(screen.getByLabelText('시작일'), '2026-08-14')
    await user.type(screen.getByLabelText('종료일'), '2026-08-14')
    await user.click(screen.getByRole('button', { name: '중식 조회' }))

    expect(await screen.findByText(/NEIS에 등록된 중식 정보가 없습니다/)).toBeInTheDocument()
  })
})

function jsonResponse(body: unknown): Response {
  return {
    ok: true,
    json: async () => body,
    headers: new Headers(),
  } as Response
}
