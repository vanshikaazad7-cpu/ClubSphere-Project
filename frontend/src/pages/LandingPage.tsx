import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import NewsGlobe from '../components/NewsGlobe'
import ScrollFilm from '../components/scrollfilm/ScrollFilm'

/* ── static content matching the editorial theme ─────────────────── */

const BRIEF_ITEMS = [
  {
    category: 'Campus Life',
    time: '2h ago',
    headline: 'Student-led sustainability initiative gains momentum',
    summary:
      'A new coalition of clubs launches a campus-wide effort to reduce waste and expand green spaces.',
  },
  {
    category: 'Community',
    time: '5h ago',
    headline: 'Cultural festival to unite voices from around the world',
    summary:
      "Music, food, and stories take center stage at this year's Global Roots Festival.",
  },
  {
    category: 'Opportunities',
    time: '7h ago',
    headline: 'New club grant program supports student innovation',
    summary:
      'The university has expanded funding to help student clubs bring bold ideas to life.',
  },
]

const AROUND_STORIES = [
  {
    date: 'Apr 22, 2025',
    category: 'Student Voices',
    title: 'How student clubs are building a kinder, more connected campus',
  },
  {
    date: 'Apr 20, 2025',
    category: 'Innovation',
    title: 'From a campus idea to a global stage',
  },
  {
    date: 'Apr 18, 2025',
    category: 'Community',
    title: 'Small clubs. Big change.',
  },
]

/* ── editorial sections ──────────────────────────────────────────── */

function EditorialHeader() {
  const { isAuthenticated, user } = useAuth()

  return (
    <header className="ed-header">
      <div className="ed-header-inner">
        <div className="ed-brand">
          <span className="ed-brand-name">ClubSphere</span>
          <span className="ed-edition">Campus culture • Vol. 01</span>
        </div>
        <nav className="ed-nav" aria-label="Campus navigation">
          <a href="#discover">Discover</a>
          <a href="#news">News</a>
          <Link to="/clubs">Clubs</Link>
          <Link to="/events">Events</Link>
        </nav>
        {isAuthenticated ? (
          <Link to="/clubs" className="ed-signin">
            {user?.full_name ? `Open App (${user.full_name.split(' ')[0]})` : 'Open App'} →
          </Link>
        ) : (
          <Link to="/login" className="ed-signin">
            Sign in
          </Link>
        )}
      </div>
    </header>
  )
}

function HeroCopy() {
  const { isAuthenticated } = useAuth()

  return (
    <div className="ed-hero-copy">
      <p className="ed-eyebrow">The university, in motion</p>
      <h1 className="ed-headline">
        Campus,
        <br />
        <em>in orbit.</em>
      </h1>
      <p className="ed-hero-intro">
        Find the people, ideas, and stories shaping student life.
      </p>
      <Link to={isAuthenticated ? '/clubs' : '/login'} className="ed-text-link">
        Explore the community <span aria-hidden="true">→</span>
      </Link>
      <div className="ed-manifesto">
        <div>
          Different people
          <br />
          Brighter perspectives
          <br />A stronger tomorrow
        </div>
        <div>
          Student clubs
          <br />
          Campus news
          <br />
          Real impact
        </div>
      </div>
    </div>
  )
}

function GlobeColumn() {
  return (
    <div className="ed-globe-col" id="discover">
      <div className="ed-globe-wrap">
        <span className="ed-globe-callout ed-callout-ideas">Ideas</span>
        <span className="ed-globe-callout ed-callout-people">People</span>
        <span className="ed-globe-callout ed-callout-stories">Stories</span>
        <NewsGlobe className="ed-globe-canvas" />
      </div>
    </div>
  )
}

function BriefSidebar() {
  const [today] = useState(() => new Date())
  const dateStr = today.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })

  return (
    <aside className="ed-brief" id="news">
      <div className="ed-brief-header">
        <h2 className="ed-brief-title">Today's brief</h2>
        <span className="ed-brief-date">{dateStr}</span>
      </div>
      {BRIEF_ITEMS.map((item) => (
        <article key={item.headline} className="ed-brief-item">
          <div className="ed-brief-meta">
            <span className="ed-brief-category">{item.category}</span>
            <span className="ed-brief-time">{item.time}</span>
          </div>
          <h3 className="ed-brief-headline">{item.headline}</h3>
          <p className="ed-brief-summary">{item.summary}</p>
        </article>
      ))}
      <Link to="/events" className="ed-brief-more">
        See campus events <span aria-hidden="true">→</span>
      </Link>
    </aside>
  )
}

function AroundCampus() {
  return (
    <section className="ed-around" id="around-campus">
      <div className="ed-around-inner">
        <h2 className="ed-around-heading">Around campus</h2>
        <div className="ed-around-stories">
          {AROUND_STORIES.map((story) => (
            <Link key={story.title} to="/clubs" className="ed-around-story">
              <div className="ed-around-meta">
                <span>{story.date}</span>
                <span className="ed-brief-category">{story.category}</span>
              </div>
              <div className="ed-around-story-title">
                <span>{story.title}</span>
                <span className="ed-around-arrow" aria-hidden="true">
                  →
                </span>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </section>
  )
}

function EditorialFooter() {
  const { isAuthenticated } = useAuth()
  const [year] = useState(() => new Date().getFullYear())

  return (
    <footer className="ed-footer">
      <span>© {year} ClubSphere · Campus, in orbit</span>
      <Link to={isAuthenticated ? '/clubs' : '/login'}>
        {isAuthenticated ? 'Open the platform →' : 'Enter the platform →'}
      </Link>
    </footer>
  )
}

/* ── main landing page ───────────────────────────────────────────── */

export default function LandingPage() {
  return (
    <div className="landing" id="top">
      <ScrollFilm />
      <main className="editorial">
        <EditorialHeader />
        <section className="ed-hero" aria-label="ClubSphere introduction">
          <HeroCopy />
          <GlobeColumn />
          <BriefSidebar />
        </section>
        <AroundCampus />
        <EditorialFooter />
      </main>
    </div>
  )
}
