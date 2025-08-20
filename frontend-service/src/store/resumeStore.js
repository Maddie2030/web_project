// src/store/resumeStore.js
import { create } from 'zustand';

export const useResumeStore = create((set) => ({
    resumeData: {
        fullName: 'MADHUSUDAN P',
        contact: {
            address: 'Pune, India 411001',
            phone: '+91 8019192030',
            email: 'madhusudanp.2a5@gmail.com',
        },
        keySkills: [
            'LINUX', 'TERRAFORM', 'KUBERNETES', 'DOCKER', 'AWS', 'AZURE', 'GCP',
            'ARGOCD', 'JENKINS', 'GIT', 'HELM', 'HASHICORP VAULT', 'ANSIBLE',
            'PROMETHEUS', 'GRAFANA', 'SONARQUBE', 'TRIVY', 'GITLAB'
        ],
        education: {
            year: '2019',
            degree: 'B. Tech',
            institution: 'CMR College of Engineering and Technology'
        },
        professionalSummary: 'DevOps Engineer with specialized in AWS cloud migration, designing, testing and provisioning infrastructure and implementing applications with security best practices. Managing and optimizing cloud resources and ensuring seamless CICD processes.Talented performer with over 5+ years of experience in IT as DevOps Engineer. Consistent team player with exemplary multitasking skills.',
        workHistory: [
            '• Extensive experience in Amazon Web Services (AWS) to create, manage, and configure services like ALB, ASG, EC2, IAM, S3, Redis, EBS, Route 53, RDS, DynamoDB, Lambda, Security Groups, and VPC, including automated deployment pipelines.',
            '• Expertise in automating CI/CD pipelines using Jenkins, integrating with tools like GitHub, Maven, Docker, SonarQube, and Slack for end-to-end build, test, and deployment automation.',
            '• Proficiency with Infrastructure as Code (IaC) and Configuration Management tools such as Terraform, Ansible, Helm, and Shell scripting for automated environment provisioning and management across AWS.',
            '• Proven experience in managing cloud environments, optimizing cost, performance, and security while enabling seamless DevOps practices and deployment automation across cloud platforms.',
            '• My hands-on experience includes executing test cases using both manual and automated scripts. I have written code to identify and address bugs while maintaining test cases based on new business specifications. Additionally, I have analysed log reports, fixed bugs in test scripts using Python, and utilized tools like Jira, GitHub.',
            '• I also have experience with VMware ESXi features including taking snapshots, high availability, fault tolerance, cloning, and templates, as well as functional testing, performance testing, and regression testing.'
        ],
        certifications: [
            '• AWS Certified Solution Architect - Professional',
            '• Docker Certified Associate(DCA)-Certified',
            '• Kubernetes Application Developer (CKAD)'
        ],
        customSections: [],
    },
    // Actions...
    setFullName: (name) => set((state) => ({ resumeData: { ...state.resumeData, fullName: name } })),
    setContactInfo: (field, value) => set((state) => ({ resumeData: { ...state.resumeData, contact: { ...state.resumeData.contact, [field]: value } } })),
    setSummary: (summary) => set((state) => ({ resumeData: { ...state.resumeData, professionalSummary: summary } })),
    setSkills: (skills) => set((state) => ({ resumeData: { ...state.resumeData, keySkills: skills } })),
    addSkill: () => set((state) => ({ resumeData: { ...state.resumeData, keySkills: [...state.resumeData.keySkills, ''] } })),
    removeSkill: (index) => set((state) => ({ resumeData: { ...state.resumeData, keySkills: state.resumeData.keySkills.filter((_, i) => i !== index) } })),
    setWorkHistory: (history) => set((state) => ({ resumeData: { ...state.resumeData, workHistory: history } })),
    addWorkHistoryEntry: () => set((state) => ({ resumeData: { ...state.resumeData, workHistory: [...state.resumeData.workHistory, ''] } })),
    removeWorkHistoryEntry: (index) => set((state) => ({ resumeData: { ...state.resumeData, workHistory: state.resumeData.workHistory.filter((_, i) => i !== index) } })),
    setCertifications: (certs) => set((state) => ({ resumeData: { ...state.resumeData, certifications: certs } })),
    addCertification: () => set((state) => ({ resumeData: { ...state.resumeData, certifications: [...state.resumeData.certifications, ''] } })),
    removeCertification: (index) => set((state) => ({ resumeData: { ...state.resumeData, certifications: state.resumeData.certifications.filter((_, i) => i !== index) } })),
    addCustomSection: () => set((state) => ({
        resumeData: {
            ...state.resumeData,
            customSections: [...state.resumeData.customSections, { id: Date.now(), title: '', content: '' }]
        }
    })),
    updateCustomSection: (id, field, value) => set((state) => ({
        resumeData: {
            ...state.resumeData,
            customSections: state.resumeData.customSections.map(section =>
                section.id === id ? { ...section, [field]: value } : section
            )
        }
    })),
    removeCustomSection: (id) => set((state) => ({
        resumeData: {
            ...state.resumeData,
            customSections: state.resumeData.customSections.filter(section => section.id !== id)
        }
    })),
}));