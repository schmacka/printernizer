# GDPR Compliance Configuration for Printernizer
# Data Protection and Privacy Implementation for German Market

## Overview

This document outlines the GDPR compliance measures implemented in Printernizer for Porcus3D's German 3D printing service based in Kornwestheim.

## Data Classification

### Personal Data Categories
1. **Customer Data**: Names, email addresses, phone numbers
2. **Business Data**: Company names, addresses, VAT numbers  
3. **Technical Data**: IP addresses, session cookies, browser fingerprints
4. **Usage Data**: Print job history, file uploads, system interactions

### Special Categories
- **None**: Printernizer does not process sensitive personal data categories

## Legal Basis for Processing

### Article 6(1) GDPR Lawful Basis
- **(b) Contract Performance**: Processing customer orders and providing 3D printing services
- **(c) Legal Obligation**: Tax records, business documentation requirements
- **(f) Legitimate Interest**: System security, fraud prevention, business analytics

### Data Retention Schedule
- **Customer Orders**: 7 years (German commercial law requirement)
- **Technical Logs**: 30 days (security monitoring)
- **Analytics Data**: 2 years (business improvement)
- **Session Data**: 24 hours (technical necessity)

## Data Subject Rights Implementation

### Right to Information (Art. 13-14)
- Privacy policy accessible at `/privacy-policy`
- Data collection notices in application UI
- Clear information about data processing purposes

### Right of Access (Art. 15)
- API endpoint: `GET /api/v1/user/{id}/data`
- Export format: JSON + PDF summary
- Response time: Maximum 30 days

### Right to Rectification (Art. 16)
- Customer portal for data updates
- API endpoint: `PUT /api/v1/user/{id}/profile`
- Automatic data validation and verification

### Right to Erasure (Art. 17)
- API endpoint: `DELETE /api/v1/user/{id}`
- Soft delete with 30-day grace period
- Permanent deletion after legal retention periods

### Right to Data Portability (Art. 20)
- Export formats: JSON, CSV, XML
- API endpoint: `GET /api/v1/user/{id}/export`
- Structured, machine-readable format

### Right to Object (Art. 21)
- Marketing opt-out mechanisms
- Analytics data processing objection
- Contact: datenschutz@porcus3d.de

## Technical and Organizational Measures

### Security Measures
1. **Encryption at Rest**: AES-256 for database files
2. **Encryption in Transit**: TLS 1.3 for all communications
3. **Access Controls**: RBAC with principle of least privilege
4. **Audit Logging**: Comprehensive access and modification logs
5. **Regular Backups**: Encrypted, versioned, geographically distributed

### Data Minimization
- Only collect data necessary for service provision
- Automatic data anonymization after retention periods
- Regular data audits and cleanup processes

### Privacy by Design
- Default privacy settings protect user data
- Opt-in consent for non-essential data processing
- Regular privacy impact assessments

## Cookie and Tracking Compliance

### Essential Cookies
- Session management: `sessionid` (24 hours)
- Security: `csrftoken` (1 year)
- Language preference: `language` (1 year)

### Analytics Cookies (Opt-in Required)
- Usage tracking: `analytics_id` (2 years)
- Performance monitoring: `performance_id` (30 days)

### Consent Management
- Cookie banner with granular choices
- Consent storage and management
- Easy consent withdrawal

## Data Processing Records (Art. 30)

### Controller Information
- **Name**: Porcus3D
- **Address**: Kornwestheim, Germany
- **Contact**: sebastian@porcus3d.de
- **DPO Contact**: datenschutz@porcus3d.de

### Processing Activities
1. **Customer Management**
   - Purpose: Order processing and customer service
   - Categories: Contact data, order history
   - Recipients: Internal staff only
   - Retention: 7 years

2. **System Operations**
   - Purpose: Service provision and security
   - Categories: Technical data, usage logs
   - Recipients: Technical staff, monitoring systems
   - Retention: 30 days

3. **Business Analytics**
   - Purpose: Service improvement and reporting
   - Categories: Aggregated usage data
   - Recipients: Management, analytics systems
   - Retention: 2 years

## Breach Response Procedures

### Detection and Assessment
1. Automated monitoring and alerting systems
2. 72-hour breach assessment timeline
3. Risk evaluation and impact analysis

### Notification Requirements
- **Supervisory Authority**: Within 72 hours if high risk
- **Data Subjects**: Without undue delay if high risk
- **Documentation**: Comprehensive incident reports

### Response Team
- **DPO**: datenschutz@porcus3d.de
- **Technical Lead**: sebastian@porcus3d.de
- **Legal Counsel**: [External legal advisor]

## Vendor and Third-Party Management

### Data Processing Agreements
All third-party processors must sign DPA agreements covering:
- Processing instructions and limitations
- Security requirements and auditing rights
- Data subject rights and breach notification
- International transfer safeguards

### Current Processors
1. **Cloud Hosting Provider**: German data center, DPA signed
2. **Monitoring Services**: EU-based, GDPR compliant
3. **Email Service**: Encrypted, German provider

## International Data Transfers

### Transfer Mechanisms
- **Adequacy Decisions**: EU/EEA processing only
- **Standard Contractual Clauses**: For any non-EU processors
- **Binding Corporate Rules**: Not applicable

### Current Transfers
- All data processing occurs within Germany/EU
- No international transfers currently implemented

## Compliance Monitoring

### Regular Audits
- Quarterly data inventory reviews
- Annual privacy impact assessments  
- Ongoing security posture evaluations

### Documentation Maintenance
- Processing record updates
- Policy and procedure reviews
- Training and awareness programs

### Contact Information

**Data Protection Officer**
Email: datenschutz@porcus3d.de
Phone: [Phone number]
Address: Porcus3D, Kornwestheim, Germany

**Supervisory Authority**
Der Landesbeauftragte für den Datenschutz und die Informationsfreiheit Baden-Württemberg
Email: poststelle@lfdi.bwl.de
Website: https://www.baden-wuerttemberg.datenschutz.de/

---
*Last Updated: September 2025*
*Version: 1.0*