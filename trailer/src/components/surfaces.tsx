/* The three surfaces, rebuilt in React at trailer resolution.

   These are drawings of the product, not screenshots of it, and they are a
   drawing on purpose: a real capture at 1080p is a wall of 15px type nobody
   reads off a projector, and cropping it to the readable part shows one card
   and no context. So the layout, the palette and the copy are the app's, and
   the type is set two or three steps larger than the app sets it.

   What is on these screens is taken from the real modules rather than
   invented: the lesson card from app/lessons.py, its citation from
   app/sources.py, the helper's three ways to send a report from docs/SCOPE.md,
   the letter from the template in app/letters.py. A trailer that shows copy
   the product does not have is a trailer that writes a cheque the demo cannot
   cash. If a screen here stops matching the app, the app is right. */

import React from "react";
import { body, c, display, grad, mono } from "../theme";
import { Mark } from "./Mark";

const Bar: React.FC<{ who: string; right?: React.ReactNode; small?: boolean }> = ({ who, right, small }) => (
  <div
    style={{
      padding: small ? "16px 22px" : "20px 30px",
      background: `linear-gradient(103deg, ${c.tealDeep} 0%, ${c.teal} 62%, #12907C 100%)`,
      display: "flex",
      alignItems: "center",
      gap: 14,
    }}
  >
    <Mark size={small ? 30 : 36} fill="#FFFFFF" />
    <div
      style={{
        fontFamily: display,
        fontWeight: 700,
        fontSize: small ? 24 : 28,
        letterSpacing: "-.015em",
        color: "#FFFFFF",
      }}
    >
      Bridge
    </div>
    <div style={{ fontFamily: body, fontSize: small ? 17 : 19, color: "#BEDFD9" }}>{who}</div>
    <div style={{ marginLeft: "auto", display: "flex", gap: 10 }}>{right}</div>
  </div>
);

const Pill: React.FC<{ children: React.ReactNode; solid?: boolean }> = ({ children, solid }) => (
  <div
    style={{
      fontFamily: body,
      fontSize: 17,
      border: `1px solid rgba(255,255,255,${solid ? ".3" : ".34"})`,
      backgroundColor: solid ? "rgba(255,255,255,.16)" : "transparent",
      borderRadius: 999,
      padding: "7px 17px",
      color: solid ? "#FFFFFF" : "#EAF6F4",
      whiteSpace: "nowrap",
    }}
  >
    {children}
  </div>
);

const Card: React.FC<{ children: React.ReactNode; style?: React.CSSProperties }> = ({ children, style }) => (
  <div
    style={{
      backgroundColor: c.surface2,
      border: `1px solid ${c.line}`,
      borderRadius: 18,
      padding: 28,
      ...style,
    }}
  >
    {children}
  </div>
);

/* The source line under a lesson card. In the app this is rendered from
   app/sources.py and a test fails if the key is not there. */
const Cited: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div
    style={{
      fontFamily: body,
      fontSize: 17,
      lineHeight: 1.45,
      color: c.muted,
      borderLeft: `3px solid ${c.tealDeep}`,
      paddingLeft: 14,
    }}
  >
    {children}
  </div>
);

const Progress: React.FC<{ value: number }> = ({ value }) => (
  <div style={{ height: 8, borderRadius: 999, backgroundColor: c.track, overflow: "hidden" }}>
    <div style={{ width: `${value * 100}%`, height: "100%", background: grad, borderRadius: 999 }} />
  </div>
);

export const TABLET = { w: 800, h: 1080 };

/* The tablet, showing the course, because the course is the first priority of
   the product and the part that keeps working after somebody goes home. */
export const TabletScreen: React.FC = () => (
  <div
    style={{
      width: TABLET.w,
      height: TABLET.h,
      backgroundColor: c.page,
      display: "flex",
      flexDirection: "column",
      overflow: "hidden",
    }}
  >
    <Bar who="Ramirez, D." right={<Pill>Sign out</Pill>} />
    <div style={{ padding: "34px 34px 0", display: "flex", flexDirection: "column", gap: 24, flexGrow: 1 }}>
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <div style={{ fontFamily: body, fontSize: 19, color: c.tealInk, letterSpacing: ".12em", textTransform: "uppercase", fontWeight: 600 }}>
          Lesson 4 of 11
        </div>
        <Progress value={0.38} />
      </div>

      <Card>
        <div style={{ fontFamily: display, fontWeight: 700, fontSize: 38, lineHeight: 1.15, letterSpacing: "-.02em", color: c.ink }}>
          120 days out, ask for the Social Security card
        </div>
        <div style={{ fontFamily: body, fontSize: 24, lineHeight: 1.5, color: c.ink2, marginTop: 20 }}>
          That is the mark. At 120 days before you go home, the Social Security card
          application goes in. If you are inside that window right now and nobody has
          raised it with you, raise it with them.
        </div>
        <div style={{ marginTop: 24 }}>
          <Cited>
            DOCCS and DMV Identification Card Program,
            <br />
            Annual Legislative Report 2025, checked 2026-09-23
          </Cited>
        </div>
      </Card>

      <div
        style={{
          fontFamily: body,
          fontSize: 21,
          lineHeight: 1.5,
          color: c.amberInk,
          backgroundColor: c.amberSoft,
          border: `1px solid ${c.amber}44`,
          borderRadius: 14,
          padding: "18px 22px",
        }}
      >
        The other 120 days is not the same 120 days. Your release ID expires 120 days
        after you walk out.
      </div>

      <div style={{ marginTop: 30, display: "flex", flexDirection: "column", gap: 12 }}>
        <div style={{ fontFamily: body, fontSize: 18, letterSpacing: ".14em", textTransform: "uppercase", color: c.muted, fontWeight: 600 }}>
          Coming up
        </div>
        {[
          "The birth certificate is free, unless you were born somewhere else",
          "The other 120 days, which is not the same 120 days",
        ].map((t) => (
          <div
            key={t}
            style={{
              fontFamily: body,
              fontSize: 21,
              color: c.faint,
              borderTop: `1px solid ${c.line}`,
              paddingTop: 12,
            }}
          >
            {t}
          </div>
        ))}
      </div>

      <div style={{ marginTop: "auto", display: "flex", gap: 14, padding: "0 0 34px" }}>
        <div
          style={{
            flexGrow: 1,
            background: grad,
            borderRadius: 999,
            padding: "20px 0",
            textAlign: "center",
            fontFamily: display,
            fontWeight: 700,
            fontSize: 25,
            color: "#04140E",
            boxShadow: "0 6px 22px rgba(45,212,160,.28)",
          }}
        >
          Next
        </div>
        <div
          style={{
            width: 220,
            border: `1px solid ${c.lineStrong}`,
            borderRadius: 999,
            padding: "20px 0",
            textAlign: "center",
            fontFamily: body,
            fontSize: 23,
            color: c.ink2,
          }}
        >
          Back
        </div>
      </div>
    </div>
  </div>
);

export const PHONE = { w: 520, h: 1060 };

/* The helper's phone. Exactly one task on screen, and the three ways a report
   can come in, in the order the product prefers them. */
export const PhoneScreen: React.FC = () => (
  <div
    style={{
      width: PHONE.w,
      height: PHONE.h,
      backgroundColor: c.page,
      display: "flex",
      flexDirection: "column",
      overflow: "hidden",
    }}
  >
    <Bar who="Helping D.R." small right={<Pill solid>Helper</Pill>} />
    <div style={{ padding: "30px 26px", display: "flex", flexDirection: "column", gap: 22, flexGrow: 1 }}>
      <div style={{ fontFamily: body, fontSize: 18, letterSpacing: ".14em", textTransform: "uppercase", color: c.tealInk, fontWeight: 600 }}>
        One thing to do
      </div>
      <div style={{ fontFamily: display, fontWeight: 700, fontSize: 36, lineHeight: 1.16, letterSpacing: "-.02em", color: c.ink }}>
        The credit report came in the mail. Send it in.
      </div>

      <Card style={{ padding: 22, display: "flex", flexDirection: "column", gap: 14 }}>
        {[
          ["Upload the PDF", "Best, if you have it"],
          ["Type what it says", "Slower, always works"],
          ["Photograph the pages", "Last resort"],
        ].map(([label, note], i) => (
          <div
            key={label}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 14,
              padding: "16px 18px",
              borderRadius: 14,
              border: `1px solid ${i === 0 ? c.teal : c.line}`,
              backgroundColor: i === 0 ? c.tealSoft : "transparent",
            }}
          >
            <div
              style={{
                width: 30,
                height: 30,
                borderRadius: 999,
                border: `2px solid ${i === 0 ? c.teal : c.lineStrong}`,
                backgroundColor: i === 0 ? c.teal : "transparent",
              }}
            />
            <div>
              <div style={{ fontFamily: body, fontWeight: 600, fontSize: 22, color: c.ink }}>{label}</div>
              <div style={{ fontFamily: body, fontSize: 17, color: c.muted }}>{note}</div>
            </div>
          </div>
        ))}
      </Card>

      <div
        style={{
          fontFamily: body,
          fontSize: 18,
          lineHeight: 1.5,
          color: c.ink2,
          border: `1px solid ${c.line}`,
          borderRadius: 14,
          padding: "16px 18px",
        }}
      >
        Bridge will never ask you for money, a password, or a Social Security number.
      </div>

      <div
        style={{
          marginTop: "auto",
          background: grad,
          borderRadius: 999,
          padding: "19px 0",
          textAlign: "center",
          fontFamily: display,
          fontWeight: 700,
          fontSize: 24,
          color: "#04140E",
        }}
      >
        Send it in
      </div>
    </div>
  </div>
);

export const DESK = { w: 1380, h: 900 };

/* The coordinator's desktop. The queue on the left sorted by what expires
   first, the drafted letter on the right, and the approval that a person and
   not the app performs. */
export const DeskScreen: React.FC = () => (
  <div
    style={{
      width: DESK.w,
      height: DESK.h,
      backgroundColor: c.page,
      display: "flex",
      flexDirection: "column",
      overflow: "hidden",
    }}
  >
    <Bar who="Coordinator, Case plan" right={<><Pill>Caseload</Pill><Pill solid>New intake</Pill></>} />
    <div style={{ display: "flex", gap: 22, padding: 26, flexGrow: 1, minHeight: 0 }}>
      <div style={{ width: 400, display: "flex", flexDirection: "column", gap: 12 }}>
        <div style={{ fontFamily: body, fontSize: 17, letterSpacing: ".14em", textTransform: "uppercase", color: c.muted, fontWeight: 600 }}>
          Soonest deadline first
        </div>
        {[
          ["Ramirez, D.", "Error on file", c.rose, "Dispute due in 11 days"],
          ["Okafor, J.", "No ID documents", c.amber, "Release in 104 days"],
          ["Bell, T.", "Credit invisible", c.sky, "Course, lesson 2"],
          ["Vargas, M.", "Debt, no error", c.green, "Obligations list"],
        ].map(([name, state, tone, when], i) => (
          <div
            key={name}
            style={{
              borderRadius: 14,
              border: `1px solid ${i === 0 ? c.lineStrong : c.line}`,
              backgroundColor: i === 0 ? c.surface2 : "transparent",
              padding: "16px 18px",
              display: "flex",
              flexDirection: "column",
              gap: 6,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <div style={{ width: 10, height: 10, borderRadius: 999, backgroundColor: tone }} />
              <div style={{ fontFamily: body, fontWeight: 600, fontSize: 22, color: c.ink }}>{name}</div>
            </div>
            <div style={{ fontFamily: body, fontSize: 18, color: c.ink2 }}>{state}</div>
            <div style={{ fontFamily: body, fontSize: 16, color: c.muted }}>{when}</div>
          </div>
        ))}
      </div>

      <Card style={{ flexGrow: 1, display: "flex", flexDirection: "column", gap: 16, minWidth: 0 }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 14 }}>
          <div style={{ fontFamily: display, fontWeight: 700, fontSize: 30, letterSpacing: "-.02em", color: c.ink }}>
            Dispute letter, draft
          </div>
          <div style={{ fontFamily: body, fontSize: 18, color: c.muted }}>1 of 3 · Equifax</div>
        </div>
        <div
          style={{
            flexGrow: 1,
            backgroundColor: c.surface,
            border: `1px solid ${c.line}`,
            borderRadius: 12,
            padding: "22px 26px",
            fontFamily: mono,
            fontSize: 18,
            lineHeight: 1.65,
            color: c.ink2,
            whiteSpace: "pre-wrap",
            overflow: "hidden",
          }}
        >
{`Re: Request to remove inaccurate information

I am writing to dispute the following information in my
file. The item listed below is not mine. I did not open
this account and I request that it be removed.

Item: Sterling Auto Finance, account ending 4471
Reason: Account opened while I was incarcerated.

I understand you have 30 days from the date you receive
this letter to complete your investigation.`}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div
            style={{
              background: grad,
              borderRadius: 999,
              padding: "16px 42px",
              fontFamily: display,
              fontWeight: 700,
              fontSize: 23,
              color: "#04140E",
            }}
          >
            Approve and print
          </div>
          <div
            style={{
              border: `1px solid ${c.lineStrong}`,
              borderRadius: 999,
              padding: "16px 34px",
              fontFamily: body,
              fontSize: 22,
              color: c.ink2,
            }}
          >
            Edit first
          </div>
          <div style={{ marginLeft: "auto", fontFamily: body, fontSize: 17, color: c.muted }}>
            Edit rate this month: 34%
          </div>
        </div>
      </Card>
    </div>
  </div>
);
