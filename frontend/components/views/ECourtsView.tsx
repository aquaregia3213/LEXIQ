'use client';

import React, { useState, useEffect } from 'react';
import {
  api,
  ECourtsCaseResult,
  ECourtsLookupResponse,
  ECourtsAnalysisResponse,
  ECourtsStatusResponse,
} from '../../lib/api';

const SAMPLE_BOMBAY_HC = `In the Court of Hon'ble Commercial Division, High Court of Judicature at Bombay
Case Type: Commercial Suit (COMM.S.) 1234 of 2023
CNR Number: MHAU010012342023
Filing Date: 14/03/2023
Registration Date: 18/03/2023
Petitioner: Apex Cloud Technologies Pvt. Ltd. Advocate: Adv. Rajesh K. Sharma
Versus
Respondent: Bharat Infra Solutions Ltd. & Ors. Advocate: Adv. Meenakshi S. Sundaram
Status: PENDING
Stage of Case: Arguments on Interim Injunction (Order 39 Rule 1 & 2 CPC)
Next Hearing Date: 12/11/2026
Purpose of Hearing: Hearing on Notice of Motion

Case History:
18/03/2023 Admit. Notice issued to respondents returnable in 4 weeks. 20/04/2023
20/04/2023 Written Statement filed by Respondent 1. Adjourned for rejoinder. 15/06/2023
15/09/2024 Part heard on Notice of Motion. Injunction continued till next date. 12/11/2026`;

const SAMPLE_DELHI_HC = `In the High Court of Delhi at New Delhi
Case Type: Arbitration Petition (O.M.P. (COMM)) 5678 of 2022
CNR Number: DLHC010056782022
Filing Date: 05/08/2022
Registration Date: 10/08/2022
Petitioner: Global Telecom Infrastructure Ltd. Advocate: Adv. Siddharth Malhotra
Versus
Respondent: National Highways Logistics Authority Advocate: Senior Standing Counsel
Status: DISPOSED
Stage of Case: Judgment Pronounced
Next Hearing Date: None
Purpose of Hearing: Disposed

Case History:
10/08/2022 Petition under Section 34 of Arbitration Act admitted. 14/11/2022
22/05/2023 Arguments concluded. Judgment reserved. 15/07/2023`;

export const ECourtsView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'search' | 'ingest' | 'results'>('search');

  // Search form state
  const [cnrNumber, setCnrNumber] = useState<string>('MHAU010012342023');
  const [caseType, setCaseType] = useState<string>('Commercial Suit');
  const [caseNumber, setCaseNumber] = useState<string>('1234');
  const [caseYear, setCaseYear] = useState<number>(2023);
  const [stateName, setStateName] = useState<string>('Maharashtra');

  // Ingest form state
  const [rawText, setRawText] = useState<string>(SAMPLE_BOMBAY_HC);

  // Results state
  const [lookupResponse, setLookupResponse] = useState<ECourtsLookupResponse | null>(null);
  const [caseData, setCaseData] = useState<ECourtsCaseResult | null>(null);
  const [analysisData, setAnalysisData] = useState<ECourtsAnalysisResponse | null>(null);
  const [statusInfo, setStatusInfo] = useState<ECourtsStatusResponse | null>(null);

  // Loading & error states
  const [loading, setLoading] = useState<boolean>(false);
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Fetch operational status on mount
  useEffect(() => {
    api.getECourtsStatus()
      .then(setStatusInfo)
      .catch((err) => console.error('Failed to fetch eCourts status:', err));
  }, []);

  const handleLookup = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);
    setAnalysisData(null);

    try {
      const res = await api.lookupECourts({
        cnr_number: cnrNumber.trim() || undefined,
        case_type: caseType.trim() || undefined,
        case_number: caseNumber.trim() || undefined,
        year: caseYear || undefined,
        state: stateName.trim() || undefined,
      });

      setLookupResponse(res);
      if (res.case_data) {
        setCaseData(res.case_data);
        setActiveTab('results');
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'eCourts lookup failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rawText.trim()) return;

    setLoading(true);
    setErrorMsg(null);
    setAnalysisData(null);

    try {
      const res = await api.ingestECourtsRecord({
        raw_text: rawText,
        source_url: 'https://services.ecourts.gov.in/ecourtindia_v6/',
      });
      setCaseData(res);
      setActiveTab('results');
    } catch (err: any) {
      setErrorMsg(err.message || 'Court record normalization failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleRunAnalysis = async () => {
    if (!caseData && !rawText) return;
    setAnalyzing(true);
    setErrorMsg(null);

    try {
      const res = await api.analyzeECourtsCase({
        case_data: caseData || undefined,
        raw_text: rawText || undefined,
        question: 'Analyze procedural posture, pending applications, hearing risks, and immediate next steps.',
      });
      setAnalysisData(res);
    } catch (err: any) {
      setErrorMsg(err.message || 'AI analysis failed.');
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '24px' }}>
      {/* Header Banner */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.8))',
        border: '1px solid rgba(148, 163, 184, 0.15)',
        borderRadius: '16px',
        padding: '24px',
        marginBottom: '24px',
        backdropFilter: 'blur(12px)',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
              <span style={{ fontSize: '28px' }}>⚖️</span>
              <h1 style={{ margin: 0, fontSize: '24px', fontWeight: '700', color: '#f8fafc' }}>
                Indian eCourts Case Intelligence
              </h1>
            </div>
            <p style={{ margin: 0, color: '#94a3b8', fontSize: '14px', maxWidth: '750px', lineHeight: '1.5' }}>
              Compliant integration targeting the official National Judicial Data Grid & eCourts Services (<code style={{ color: '#38bdf8' }}>services.ecourts.gov.in</code>).
              Generates verified portal coordinates, normalizes lawful court records, and performs evidence-grounded procedural risk analysis without unauthorized scraping.
            </p>
          </div>

          {/* Integration Status Badges */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', minWidth: '260px' }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '6px 12px',
              background: 'rgba(16, 185, 129, 0.1)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              borderRadius: '8px',
              color: '#34d399',
              fontSize: '12px',
              fontWeight: '600',
            }}>
              <span>●</span> Official Portal Link Available
            </div>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '6px 12px',
              background: 'rgba(245, 158, 11, 0.1)',
              border: '1px solid rgba(245, 158, 11, 0.3)',
              borderRadius: '8px',
              color: '#fbbf24',
              fontSize: '12px',
              fontWeight: '600',
            }}>
              <span>⚠️</span> Visual CAPTCHA Active (Manual Lookup Required)
            </div>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '6px 12px',
              background: 'rgba(99, 102, 241, 0.1)',
              border: '1px solid rgba(99, 102, 241, 0.3)',
              borderRadius: '8px',
              color: '#a5b4fc',
              fontSize: '12px',
              fontWeight: '600',
            }}>
              <span>🏛️</span> Mode: {statusInfo?.integration_mode?.toUpperCase() || 'PORTAL_ASSISTED'}
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '20px', borderBottom: '1px solid rgba(148, 163, 184, 0.2)', paddingBottom: '8px' }}>
        <button
          onClick={() => setActiveTab('search')}
          style={{
            padding: '10px 20px',
            borderRadius: '8px',
            border: 'none',
            background: activeTab === 'search' ? '#2563eb' : 'transparent',
            color: activeTab === 'search' ? '#fff' : '#94a3b8',
            fontWeight: '600',
            cursor: 'pointer',
            transition: 'all 0.2s',
          }}
        >
          🔍 1. Search Portal Coordinates
        </button>
        <button
          onClick={() => setActiveTab('ingest')}
          style={{
            padding: '10px 20px',
            borderRadius: '8px',
            border: 'none',
            background: activeTab === 'ingest' ? '#2563eb' : 'transparent',
            color: activeTab === 'ingest' ? '#fff' : '#94a3b8',
            fontWeight: '600',
            cursor: 'pointer',
            transition: 'all 0.2s',
          }}
        >
          📋 2. Lawful Record Intake
        </button>
        <button
          onClick={() => setActiveTab('results')}
          style={{
            padding: '10px 20px',
            borderRadius: '8px',
            border: 'none',
            background: activeTab === 'results' ? '#2563eb' : 'transparent',
            color: activeTab === 'results' ? '#fff' : '#94a3b8',
            fontWeight: '600',
            cursor: 'pointer',
            transition: 'all 0.2s',
          }}
        >
          📊 3. Case Record & AI Analysis
        </button>
      </div>

      {errorMsg && (
        <div style={{
          padding: '12px 16px',
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          borderRadius: '8px',
          color: '#f87171',
          marginBottom: '20px',
          fontSize: '14px',
        }}>
          ❌ {errorMsg}
        </div>
      )}

      {/* Tab 1: Search Portal Coordinates */}
      {activeTab === 'search' && (
        <div style={{
          background: 'var(--bg-secondary, #1e293b)',
          border: '1px solid var(--border-color, rgba(148, 163, 184, 0.15))',
          borderRadius: '16px',
          padding: '24px',
        }}>
          <h3 style={{ margin: '0 0 16px 0', color: '#f8fafc', fontSize: '18px' }}>
            Official Case Coordinates & Portal Lookup
          </h3>
          <p style={{ color: '#94a3b8', fontSize: '14px', marginBottom: '20px' }}>
            Enter a standard 16-character Indian CNR number or Case Details. LEXIQ validates the format, prepares the official portal URL, and provides guidance for CAPTCHA verification.
          </p>

          <form onSubmit={handleLookup} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px' }}>
            <div>
              <label style={{ display: 'block', color: '#cbd5e1', fontSize: '13px', fontWeight: '600', marginBottom: '6px' }}>
                CNR Number (16 characters)
              </label>
              <input
                type="text"
                value={cnrNumber}
                onChange={(e) => setCnrNumber(e.target.value.toUpperCase())}
                placeholder="e.g. MHAU010012342023"
                maxLength={16}
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  background: 'rgba(15, 23, 42, 0.6)',
                  border: '1px solid rgba(148, 163, 184, 0.25)',
                  borderRadius: '8px',
                  color: '#f8fafc',
                  fontFamily: 'monospace',
                  fontSize: '15px',
                }}
              />
              <span style={{ fontSize: '11px', color: '#64748b' }}>
                State (2) + District (2) + Court Complex (2) + Case No (6) + Year (4)
              </span>
            </div>

            <div>
              <label style={{ display: 'block', color: '#cbd5e1', fontSize: '13px', fontWeight: '600', marginBottom: '6px' }}>
                State Jurisdiction
              </label>
              <input
                type="text"
                value={stateName}
                onChange={(e) => setStateName(e.target.value)}
                placeholder="e.g. Maharashtra, Delhi, Karnataka"
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  background: 'rgba(15, 23, 42, 0.6)',
                  border: '1px solid rgba(148, 163, 184, 0.25)',
                  borderRadius: '8px',
                  color: '#f8fafc',
                  fontSize: '14px',
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', color: '#cbd5e1', fontSize: '13px', fontWeight: '600', marginBottom: '6px' }}>
                Case Type
              </label>
              <input
                type="text"
                value={caseType}
                onChange={(e) => setCaseType(e.target.value)}
                placeholder="e.g. COMM.S., ARB.P., WP, CS"
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  background: 'rgba(15, 23, 42, 0.6)',
                  border: '1px solid rgba(148, 163, 184, 0.25)',
                  borderRadius: '8px',
                  color: '#f8fafc',
                  fontSize: '14px',
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', color: '#cbd5e1', fontSize: '13px', fontWeight: '600', marginBottom: '6px' }}>
                Case Number & Year
              </label>
              <div style={{ display: 'flex', gap: '8px' }}>
                <input
                  type="text"
                  value={caseNumber}
                  onChange={(e) => setCaseNumber(e.target.value)}
                  placeholder="Number"
                  style={{
                    flex: 1,
                    padding: '10px 14px',
                    background: 'rgba(15, 23, 42, 0.6)',
                    border: '1px solid rgba(148, 163, 184, 0.25)',
                    borderRadius: '8px',
                    color: '#f8fafc',
                    fontSize: '14px',
                  }}
                />
                <input
                  type="number"
                  value={caseYear}
                  onChange={(e) => setCaseYear(parseInt(e.target.value) || 2023)}
                  placeholder="Year"
                  style={{
                    width: '100px',
                    padding: '10px 14px',
                    background: 'rgba(15, 23, 42, 0.6)',
                    border: '1px solid rgba(148, 163, 184, 0.25)',
                    borderRadius: '8px',
                    color: '#f8fafc',
                    fontSize: '14px',
                  }}
                />
              </div>
            </div>

            <div style={{ gridColumn: '1 / -1', marginTop: '10px', display: 'flex', gap: '12px' }}>
              <button
                type="submit"
                disabled={loading}
                style={{
                  padding: '12px 24px',
                  background: '#2563eb',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '8px',
                  fontWeight: '600',
                  fontSize: '14px',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  boxShadow: '0 4px 12px rgba(37, 99, 235, 0.3)',
                }}
              >
                {loading ? 'Validating Coordinates...' : 'Generate Official Portal Link'}
              </button>
            </div>
          </form>

          {lookupResponse && (
            <div style={{
              marginTop: '24px',
              padding: '20px',
              background: 'rgba(15, 23, 42, 0.7)',
              border: '1px solid rgba(148, 163, 184, 0.2)',
              borderRadius: '12px',
            }}>
              <h4 style={{ margin: '0 0 10px 0', color: '#38bdf8', fontSize: '16px' }}>
                Official Portal Search Ready
              </h4>
              <p style={{ color: '#cbd5e1', fontSize: '14px', lineHeight: '1.5', margin: '0 0 16px 0' }}>
                {lookupResponse.message}
              </p>

              <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                <a
                  href={lookupResponse.portal_search_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '10px 20px',
                    background: 'linear-gradient(135deg, #059669, #10b981)',
                    color: '#fff',
                    textDecoration: 'none',
                    borderRadius: '8px',
                    fontWeight: '600',
                    fontSize: '14px',
                    boxShadow: '0 4px 12px rgba(16, 185, 129, 0.25)',
                  }}
                >
                  🚀 Open Official eCourts Portal (services.ecourts.gov.in)
                </a>
              </div>

              {lookupResponse.suggested_actions?.length > 0 && (
                <div style={{ marginTop: '16px', borderTop: '1px solid rgba(148, 163, 184, 0.1)', paddingTop: '12px' }}>
                  <span style={{ fontSize: '12px', color: '#94a3b8', fontWeight: '600' }}>Next Steps:</span>
                  <ul style={{ margin: '6px 0 0 0', paddingLeft: '20px', color: '#cbd5e1', fontSize: '13px' }}>
                    {lookupResponse.suggested_actions.map((act, i) => (
                      <li key={i}>{act}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Lawful Record Intake */}
      {activeTab === 'ingest' && (
        <div style={{
          background: 'var(--bg-secondary, #1e293b)',
          border: '1px solid var(--border-color, rgba(148, 163, 184, 0.15))',
          borderRadius: '16px',
          padding: '24px',
        }}>
          <h3 style={{ margin: '0 0 12px 0', color: '#f8fafc', fontSize: '18px' }}>
            Lawful Court Record & Judgment Intake
          </h3>
          <p style={{ color: '#94a3b8', fontSize: '14px', marginBottom: '16px' }}>
            Paste the official case status printout, cause list text, or interim order downloaded from the eCourts portal. LEXIQ extracts dates, parties, and procedural status for AI analysis.
          </p>

          <div style={{ display: 'flex', gap: '10px', marginBottom: '16px' }}>
            <button
              type="button"
              onClick={() => setRawText(SAMPLE_BOMBAY_HC)}
              style={{
                padding: '6px 14px',
                background: 'rgba(56, 189, 248, 0.1)',
                border: '1px solid rgba(56, 189, 248, 0.3)',
                borderRadius: '6px',
                color: '#38bdf8',
                fontSize: '12px',
                cursor: 'pointer',
              }}
            >
              Load Sample: Bombay HC Commercial Suit
            </button>
            <button
              type="button"
              onClick={() => setRawText(SAMPLE_DELHI_HC)}
              style={{
                padding: '6px 14px',
                background: 'rgba(168, 85, 247, 0.1)',
                border: '1px solid rgba(168, 85, 247, 0.3)',
                borderRadius: '6px',
                color: '#c084fc',
                fontSize: '12px',
                cursor: 'pointer',
              }}
            >
              Load Sample: Delhi HC Arbitration Petition
            </button>
          </div>

          <form onSubmit={handleIngest}>
            <textarea
              rows={12}
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
              placeholder="Paste case status response or order text here..."
              style={{
                width: '100%',
                padding: '14px',
                background: 'rgba(15, 23, 42, 0.6)',
                border: '1px solid rgba(148, 163, 184, 0.25)',
                borderRadius: '10px',
                color: '#f8fafc',
                fontFamily: 'monospace',
                fontSize: '13px',
                lineHeight: '1.5',
                marginBottom: '16px',
              }}
            />

            <button
              type="submit"
              disabled={loading}
              style={{
                padding: '12px 24px',
                background: '#2563eb',
                color: '#fff',
                border: 'none',
                borderRadius: '8px',
                fontWeight: '600',
                fontSize: '14px',
                cursor: loading ? 'not-allowed' : 'pointer',
              }}
            >
              {loading ? 'Normalizing Court Record...' : 'Normalize & Inspect Case Record'}
            </button>
          </form>
        </div>
      )}

      {/* Tab 3: Case Record & AI Analysis */}
      {activeTab === 'results' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Official Facts Card */}
          <div style={{
            background: 'var(--bg-secondary, #1e293b)',
            border: '1px solid var(--border-color, rgba(148, 163, 184, 0.15))',
            borderRadius: '16px',
            padding: '24px',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px', marginBottom: '16px' }}>
              <div>
                <span style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#38bdf8', fontWeight: '700' }}>
                  Verified Official Record
                </span>
                <h3 style={{ margin: '4px 0', fontSize: '20px', color: '#f8fafc' }}>
                  {caseData?.case_type || 'Case Record'} {caseData?.case_number ? `${caseData.case_number}/${caseData.filing_year}` : ''}
                </h3>
                <p style={{ margin: 0, color: '#94a3b8', fontSize: '14px' }}>
                  {caseData?.court_name || 'Indian Judicial System'}
                </p>
              </div>

              <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                <span style={{
                  padding: '6px 14px',
                  borderRadius: '20px',
                  fontSize: '12px',
                  fontWeight: '700',
                  background: caseData?.status === 'DISPOSED' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(234, 179, 8, 0.2)',
                  color: caseData?.status === 'DISPOSED' ? '#34d399' : '#facc15',
                  border: `1px solid ${caseData?.status === 'DISPOSED' ? '#059669' : '#ca8a04'}`,
                }}>
                  {caseData?.status || 'PENDING'}
                </span>

                <button
                  onClick={handleRunAnalysis}
                  disabled={analyzing}
                  style={{
                    padding: '8px 18px',
                    background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                    color: '#fff',
                    border: 'none',
                    borderRadius: '8px',
                    fontSize: '13px',
                    fontWeight: '600',
                    cursor: analyzing ? 'not-allowed' : 'pointer',
                    boxShadow: '0 4px 12px rgba(99, 102, 241, 0.3)',
                  }}
                >
                  {analyzing ? 'Analyzing with AI...' : '🤖 Run AI Procedural Risk Analysis'}
                </button>
              </div>
            </div>

            {/* Core Details Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '20px' }}>
              <div style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '12px', borderRadius: '8px' }}>
                <span style={{ fontSize: '11px', color: '#64748b', display: 'block' }}>CNR NUMBER</span>
                <span style={{ fontSize: '14px', color: '#f8fafc', fontWeight: '600', fontFamily: 'monospace' }}>
                  {caseData?.cnr_number || 'Not provided'}
                </span>
              </div>
              <div style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '12px', borderRadius: '8px' }}>
                <span style={{ fontSize: '11px', color: '#64748b', display: 'block' }}>NEXT HEARING DATE</span>
                <span style={{ fontSize: '14px', color: caseData?.next_hearing_date ? '#38bdf8' : '#94a3b8', fontWeight: '600' }}>
                  {caseData?.next_hearing_date || 'None scheduled / Disposed'}
                </span>
              </div>
              <div style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '12px', borderRadius: '8px' }}>
                <span style={{ fontSize: '11px', color: '#64748b', display: 'block' }}>STAGE OF CASE</span>
                <span style={{ fontSize: '13px', color: '#f8fafc', fontWeight: '500' }}>
                  {caseData?.stage_of_case || 'Hearing in progress'}
                </span>
              </div>
              <div style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '12px', borderRadius: '8px' }}>
                <span style={{ fontSize: '11px', color: '#64748b', display: 'block' }}>FILING DATE</span>
                <span style={{ fontSize: '14px', color: '#f8fafc', fontWeight: '500' }}>
                  {caseData?.filing_date || 'N/A'}
                </span>
              </div>
            </div>

            {/* Parties Details */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
              <div style={{ background: 'rgba(15, 23, 42, 0.4)', padding: '14px', borderRadius: '10px', borderLeft: '3px solid #3b82f6' }}>
                <span style={{ fontSize: '12px', color: '#60a5fa', fontWeight: '700' }}>PETITIONER / PLAINTIFF</span>
                <p style={{ margin: '4px 0 2px 0', fontSize: '14px', color: '#f8fafc', fontWeight: '600' }}>
                  {caseData?.petitioner || 'Not explicitly stated'}
                </p>
                {caseData?.petitioner_advocate && (
                  <span style={{ fontSize: '12px', color: '#94a3b8' }}>Advocate: {caseData.petitioner_advocate}</span>
                )}
              </div>
              <div style={{ background: 'rgba(15, 23, 42, 0.4)', padding: '14px', borderRadius: '10px', borderLeft: '3px solid #f97316' }}>
                <span style={{ fontSize: '12px', color: '#fb923c', fontWeight: '700' }}>RESPONDENT / DEFENDANT</span>
                <p style={{ margin: '4px 0 2px 0', fontSize: '14px', color: '#f8fafc', fontWeight: '600' }}>
                  {caseData?.respondent || 'Not explicitly stated'}
                </p>
                {caseData?.respondent_advocate && (
                  <span style={{ fontSize: '12px', color: '#94a3b8' }}>Advocate: {caseData.respondent_advocate}</span>
                )}
              </div>
            </div>

            {/* Hearing History Table */}
            {caseData?.history && caseData.history.length > 0 && (
              <div>
                <h4 style={{ margin: '0 0 10px 0', fontSize: '14px', color: '#e2e8f0', fontWeight: '600' }}>
                  Recorded Procedural History
                </h4>
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px', color: '#cbd5e1' }}>
                    <thead>
                      <tr style={{ background: 'rgba(15, 23, 42, 0.8)', borderBottom: '1px solid rgba(148, 163, 184, 0.2)' }}>
                        <th style={{ padding: '8px 12px', textAlign: 'left' }}>Hearing Date</th>
                        <th style={{ padding: '8px 12px', textAlign: 'left' }}>Business Recorded</th>
                        <th style={{ padding: '8px 12px', textAlign: 'left' }}>Next Date</th>
                      </tr>
                    </thead>
                    <tbody>
                      {caseData.history.map((h, i) => (
                        <tr key={i} style={{ borderBottom: '1px solid rgba(148, 163, 184, 0.1)' }}>
                          <td style={{ padding: '8px 12px', whiteSpace: 'nowrap', fontWeight: '600' }}>{h.hearing_date}</td>
                          <td style={{ padding: '8px 12px' }}>{h.business_recorded}</td>
                          <td style={{ padding: '8px 12px', whiteSpace: 'nowrap', color: '#38bdf8' }}>{h.next_date || '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>

          {/* AI Analysis Section */}
          {analysisData && (
            <div style={{
              background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.9))',
              border: '1px solid rgba(99, 102, 241, 0.3)',
              borderRadius: '16px',
              padding: '24px',
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.25)',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '20px' }}>🤖</span>
                  <h3 style={{ margin: 0, fontSize: '18px', color: '#f8fafc' }}>
                    AI Procedural & Litigation Risk Synthesis
                  </h3>
                </div>
                <div style={{
                  padding: '4px 12px',
                  borderRadius: '12px',
                  fontSize: '12px',
                  fontWeight: '700',
                  background: analysisData.legal_risk_level === 'HIGH' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(59, 130, 246, 0.2)',
                  color: analysisData.legal_risk_level === 'HIGH' ? '#f87171' : '#60a5fa',
                  border: `1px solid ${analysisData.legal_risk_level === 'HIGH' ? '#ef4444' : '#3b82f6'}`,
                }}>
                  RISK LEVEL: {analysisData.legal_risk_level}
                </div>
              </div>

              {/* AI Narrative */}
              <div style={{
                background: 'rgba(15, 23, 42, 0.6)',
                padding: '16px',
                borderRadius: '10px',
                color: '#e2e8f0',
                fontSize: '14px',
                lineHeight: '1.6',
                marginBottom: '20px',
                whiteSpace: 'pre-wrap',
              }}>
                {analysisData.ai_summary}
              </div>

              {/* Milestones & Next Steps */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px', marginBottom: '16px' }}>
                <div style={{ background: 'rgba(15, 23, 42, 0.4)', padding: '14px', borderRadius: '8px' }}>
                  <span style={{ fontSize: '13px', color: '#38bdf8', fontWeight: '700' }}>📌 Key Milestones</span>
                  <ul style={{ margin: '8px 0 0 0', paddingLeft: '18px', color: '#cbd5e1', fontSize: '13px', lineHeight: '1.5' }}>
                    {analysisData.key_milestones.map((m, i) => (
                      <li key={i}>{m}</li>
                    ))}
                  </ul>
                </div>
                <div style={{ background: 'rgba(15, 23, 42, 0.4)', padding: '14px', borderRadius: '8px' }}>
                  <span style={{ fontSize: '13px', color: '#34d399', fontWeight: '700' }}>⚡ Procedural Next Steps</span>
                  <ul style={{ margin: '8px 0 0 0', paddingLeft: '18px', color: '#cbd5e1', fontSize: '13px', lineHeight: '1.5' }}>
                    {analysisData.next_steps.map((s, i) => (
                      <li key={i}>{s}</li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Citation Footer */}
              <div style={{
                borderTop: '1px solid rgba(148, 163, 184, 0.15)',
                paddingTop: '12px',
                fontSize: '11px',
                color: '#94a3b8',
                display: 'flex',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '8px',
              }}>
                <span>Source: {analysisData.source_citation}</span>
                <span>Retrieved: {caseData?.retrieved_at}</span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
