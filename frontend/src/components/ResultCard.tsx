import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  PhoneIcon,
  MailIcon,
  GraduationCapIcon,
  BriefcaseIcon,
  StarIcon,
} from "lucide-react";

interface CandidateData {
  id: number;
  name: string;
  email?: string;
  phone?: string;
  experience_years?: number;
  skills: string[];
  education_summary?: string;
  professional_summary?: string;
  distance: number;
}

interface ResultCardProps {
  candidate: CandidateData;
  index: number;
}

export default function ResultCard({ candidate, index }: ResultCardProps) {
  return (
    <Card className="w-full h-full flex flex-col">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-xl font-semibold text-primary">
            {candidate.name}
          </CardTitle>
          <div className="flex items-center gap-1">
            <StarIcon className="w-4 h-4 text-yellow-500 fill-current" />
            <span className="text-sm text-muted-foreground">
              {/* Lower distance is better */}
              Match: {((1 / (1 + candidate.distance)) * 100).toFixed(0)}%
            </span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4 flex-grow">
        {/* Contact Information */}
        <div className="grid grid-cols-1 gap-3">
          {candidate.email && (
            <div className="flex items-center gap-2 text-sm">
              <MailIcon className="w-4 h-4 text-muted-foreground" />
              <span className="font-medium">{candidate.email}</span>
            </div>
          )}

          {candidate.phone && (
            <div className="flex items-center gap-2 text-sm">
              <PhoneIcon className="w-4 h-4 text-muted-foreground" />
              <span className="font-medium">{candidate.phone}</span>
            </div>
          )}
        </div>

        {/* Education */}
        {candidate.education_summary && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-medium">
              <GraduationCapIcon className="w-4 h-4 text-muted-foreground" />
              <span>Education</span>
            </div>
            <p className="text-sm text-muted-foreground ml-6">
              {candidate.education_summary}
            </p>
          </div>
        )}

        {/* Experience */}
        {(candidate.professional_summary || candidate.experience_years) && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-medium">
              <BriefcaseIcon className="w-4 h-4 text-muted-foreground" />
              <span>Experience</span>
            </div>
            {candidate.experience_years !== null &&
              candidate.experience_years !== undefined && (
                <p className="text-sm text-muted-foreground ml-6">
                  <span className="font-medium">
                    {candidate.experience_years}
                  </span>{" "}
                  years of experience
                </p>
              )}
            {candidate.professional_summary && (
              <p className="text-sm text-muted-foreground ml-6">
                {candidate.professional_summary}
              </p>
            )}
          </div>
        )}

        {/* Skills */}
        {candidate.skills && candidate.skills.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium">Skills</h4>
            <div className="flex flex-wrap gap-1">
              {candidate.skills.map((skill, idx) => (
                <Badge key={idx} variant="secondary" className="text-xs">
                  {skill.trim()}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// Function to parse LLM response into structured data
export function parseLLMResponse(response: string): CandidateData[] {
  const candidates: CandidateData[] = [];

  // Handle different response formats
  if (response.includes("- **") && response.includes("**:")) {
    // Format: - **NAME** with indented sections
    const candidate = parseIndentedFormat(response);
    if (candidate.name) {
      candidates.push(candidate);
    }
  } else if (response.includes("**") && response.includes("**")) {
    // Format: **NAME** sections
    const sections = response.split(/(?=\*\*[A-Z][A-Z\s]+\*\*)/g);

    sections.forEach((section) => {
      if (section.trim()) {
        const candidate = parseCandidateSection(section);
        if (candidate.name) {
          candidates.push(candidate);
        }
      }
    });
  } else {
    // Fallback: treat entire response as one candidate
    const candidate = parseFallbackFormat(response);
    if (candidate.name) {
      candidates.push(candidate);
    }
  }

  return candidates;
}

function parseCandidateSection(section: string): CandidateData {
  const candidate: CandidateData = {
    name: "",
    email: "",
    phone: "",
    cgpa: "",
    percentage: "",
    education: "",
    experience: "",
    skills: [],
    additionalInfo: "",
  };

  // Extract name (first bold section)
  const nameMatch = section.match(/\*\*([A-Z][A-Z\s]+)\*\*/);
  if (nameMatch) {
    candidate.name = nameMatch[1].trim();
  }

  // Extract email
  const emailMatch = section.match(/\*\*Email\*\*:\s*([^\n]+)/);
  if (emailMatch) {
    candidate.email = emailMatch[1].trim();
  }

  // Extract phone
  const phoneMatch = section.match(/\*\*Phone\*\*:\s*([^\n]+)/);
  if (phoneMatch) {
    candidate.phone = phoneMatch[1].trim();
  }

  // Extract CGPA
  const cgpaMatch = section.match(/CGPA[^\d]*(\d+\.?\d*)/);
  if (cgpaMatch) {
    candidate.cgpa = cgpaMatch[1];
  }

  // Extract percentage
  const percentageMatch = section.match(/(\d+)%/);
  if (percentageMatch) {
    candidate.percentage = percentageMatch[1] + "%";
  }

  // Extract education
  const educationMatch = section.match(
    /\*\*.*?Education.*?\*\*[:\s]*([^\n]+(?:\n(?!\*\*[A-Z]).*)*)/,
  );
  if (educationMatch) {
    candidate.education = educationMatch[1].trim();
  }

  // Extract experience
  const experienceMatch = section.match(
    /\*\*.*?Experience.*?\*\*[:\s]*([^\n]+(?:\n(?!\*\*[A-Z]|\*\*Skills).*)*)/,
  );
  if (experienceMatch) {
    candidate.experience = experienceMatch[1].trim();
  }

  // Extract skills
  const skillsMatch = section.match(/\*\*Skills\*\*[:\s]*([^\n]+)/);
  if (skillsMatch) {
    candidate.skills = skillsMatch[1]
      .split(",")
      .map((s) => s.trim())
      .filter((s) => s);
  }

  // Everything else as additional info
  const lines = section
    .split("\n")
    .filter((line) => line.trim() && !line.includes("**"));
  candidate.additionalInfo = lines.join(" ").trim();

  return candidate;
}

// Parse indented format like the user's example
function parseIndentedFormat(response: string): CandidateData {
  const candidate: CandidateData = {
    name: "",
    email: "",
    phone: "",
    cgpa: "",
    percentage: "",
    education: "",
    experience: "",
    skills: [],
    additionalInfo: "",
  };

  // Extract name from first bold section
  const nameMatch = response.match(/\*\*([A-Z][A-Z\s]+)\*\*/);
  if (nameMatch) {
    candidate.name = nameMatch[1].trim();
  }

  // Extract email
  const emailMatch = response.match(/\*\*Email\*\*:\s*([^\n]+)/);
  if (emailMatch) {
    candidate.email = emailMatch[1].trim();
  }

  // Extract phone
  const phoneMatch = response.match(/\*\*Phone\*\*:\s*([^\n]+)/);
  if (phoneMatch) {
    candidate.phone = phoneMatch[1].trim();
  }

  // Extract CGPA
  const cgpaMatch = response.match(/CGPA[^\d]*(\d+\.?\d*)/);
  if (cgpaMatch) {
    candidate.cgpa = cgpaMatch[1];
  }

  // Extract percentage
  const percentageMatch = response.match(/(\d+)%/);
  if (percentageMatch) {
    candidate.percentage = percentageMatch[1] + "%";
  }

  // Extract education details
  const educationSection = response.match(
    /\*\*.*?Education.*?\*\*.*?([^\n]+(?:\n(?!\*\*).*)*)/,
  );
  if (educationSection) {
    candidate.education = educationSection[1].trim().replace(/^\s*-\s*/, "");
  }

  // Extract experience
  const experienceSection = response.match(
    /\*\*.*?Experience.*?\*\*.*?([^\n]+(?:\n(?!\*\*|This candidate).*)*)/,
  );
  if (experienceSection) {
    candidate.experience = experienceSection[1].trim().replace(/^\s*-\s*/, "");
  }

  // Extract skills
  const skillsSection = response.match(/\*\*Skills\*\*[:\s]*([^\n]+)/);
  if (skillsSection) {
    candidate.skills = skillsSection[1]
      .split(",")
      .map((s) => s.trim())
      .filter((s) => s);
  }

  // Extract additional information
  const additionalSection = response.match(/This candidate has[^.]*\./);
  if (additionalSection) {
    candidate.additionalInfo = additionalSection[0];
  }

  return candidate;
}

// Fallback parsing for other formats
function parseFallbackFormat(response: string): CandidateData {
  const candidate: CandidateData = {
    name: "Candidate",
    email: "",
    phone: "",
    cgpa: "",
    percentage: "",
    education: "",
    experience: "",
    skills: [],
    additionalInfo: response,
  };

  // Try to extract name if it's in the response
  const nameMatch = response.match(/([A-Z][A-Z\s]{2,})/);
  if (nameMatch) {
    candidate.name = nameMatch[1].trim();
  }

  // Try to extract email
  const emailMatch = response.match(
    /([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/,
  );
  if (emailMatch) {
    candidate.email = emailMatch[1];
  }

  // Try to extract skills
  const skillsSection = response.match(/Skills[:\s]*([^\n.]+)/);
  if (skillsSection) {
    candidate.skills = skillsSection[1]
      .split(",")
      .map((s) => s.trim())
      .filter((s) => s);
  }

  return candidate;
}
