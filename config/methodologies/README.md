# PKM Methodologies

This directory contains configuration files for different Personal Knowledge Management (PKM) methodologies supported by the wep4you-agent-skills plugin.

## Available Methodologies

### 1. LYT-ACE (Linking Your Thinking + ACE Framework)
**File:** `lyt-ace.yaml`
**Author:** Nick Milo
**Best for:** Creative thinkers, writers, researchers who value flexible navigation and emergent structure

**Key Features:**
- **Atlas/** - Maps, Dots (evergreen notes), and Scopes for navigation
- **Calendar/** - Daily, weekly, monthly temporal anchors
- **Efforts/** - Active Projects and Areas of responsibility
- **Extras/** - Reference material and resources
- **Spaces/** - Domain-specific knowledge areas

**Philosophy:** Combines flexible linking with structured navigation. The ACE framework (Add, Connect, Express) guides the workflow from capture through connection to creative output.

**Use when:**
- You think in networks and connections
- You want both structure and flexibility
- You're doing creative or research work
- You value navigation and discoverability

---

### 2. PARA (Projects, Areas, Resources, Archives)
**File:** `para.yaml`
**Author:** Tiago Forte
**Best for:** Action-oriented individuals, productivity enthusiasts, project managers

**Key Features:**
- **Projects/** - Short-term efforts with clear goals and deadlines
- **Areas/** - Long-term responsibilities to maintain
- **Resources/** - Reference material on topics of interest
- **Archives/** - Inactive items from other categories

**Philosophy:** Organizes everything by actionability. Clear distinctions between active projects (with deadlines), ongoing areas (with standards), passive resources, and archived material.

**Use when:**
- You manage multiple projects
- You want clarity on what requires action
- You value productivity and GTD principles
- You need clear project/reference separation

---

### 3. Zettelkasten (Slip-Box Method)
**File:** `zettelkasten.yaml`
**Author:** Niklas Luhmann
**Best for:** Researchers, academics, deep thinkers, writers building long-term knowledge

**Key Features:**
- **Zettelkasten/** - Flat structure with timestamp IDs (YYYYMMDDHHMMSS)
- **Inbox/** - Temporary capture area
- **References/** - Literature notes and sources
- **Indexes/** - Structure notes and hubs for navigation

**Philosophy:** Atomic notes (one idea each) with dense linking. Knowledge emerges from connections. Minimal folders, maximum links. Folgezettel (continuation notes) build argument chains.

**Use when:**
- You're building a long-term knowledge base
- You value deep thinking and idea development
- You want to generate insights from connections
- You're doing academic or research work

---

### 4. Minimal (Bottom-Up, Emergence-Focused)
**File:** `minimal.yaml`
**Author:** Inspired by Kepano and emergent note-taking
**Best for:** Minimalists, beginners, those seeking simplicity and low friction

**Key Features:**
- **Inbox/** - Optional quick capture area
- **Archive/** - Optional storage for inactive notes
- **Root folder** - Most notes live here
- **Tags over folders** - Primary organization method

**Philosophy:** Start simple, let structure emerge organically. Minimal predefined structure. Fast capture without friction. Bottom-up organization based on actual use, not planned categories.

**Use when:**
- You're new to PKM and want to start simple
- You value low friction and fast capture
- You prefer tags over folder hierarchies
- You want maximum flexibility
- You're unsure which system fits you yet

---

## Choosing a Methodology

### Decision Guide

**Choose LYT-ACE if you:**
- Think in networks and connections
- Value both structure and flexibility
- Do creative or research work
- Like visual navigation (maps, graphs)

**Choose PARA if you:**
- Manage multiple projects and tasks
- Want clear action/reference separation
- Value productivity and efficiency
- Need project tracking with deadlines

**Choose Zettelkasten if you:**
- Build long-term knowledge for research/writing
- Value atomic notes and deep connections
- Want to generate new insights from linking
- Have time for thoughtful note processing

**Choose Minimal if you:**
- Want to start simple and evolve
- Prefer tags over folders
- Value low friction capture
- Want maximum portability
- Are still exploring what works for you

### Comparison Matrix

| Feature | LYT-ACE | PARA | Zettelkasten | Minimal |
|---------|---------|------|--------------|---------|
| **Structure** | Moderate | High | Low (flat) | Very Low |
| **Folders** | Multiple | 4 core | Minimal | 0-2 |
| **Learning Curve** | Medium | Low | High | Very Low |
| **Flexibility** | High | Medium | Very High | Very High |
| **Action-Oriented** | Medium | Very High | Low | Medium |
| **Research-Oriented** | High | Low | Very High | Medium |
| **Maintenance** | Medium | Medium | High | Very Low |
| **Linking Emphasis** | High | Low | Very High | Medium |

---

## Using Methodology Configurations

### Loading a Methodology

The wep4you-agent-skills plugin can load these methodology configurations to:

1. **Validate vault structure** against the methodology's folder requirements
2. **Suggest improvements** based on methodology best practices
3. **Auto-create missing folders** with proper structure
4. **Validate note types** and their properties
5. **Check linking patterns** against methodology conventions
6. **Provide workflow guidance** from the methodology definition

### Configuration Structure

Each methodology YAML file contains:

- `name` - Methodology name
- `description` - Brief description
- `author` - Creator/origin
- `url` - Reference URL for more information
- `folders` - Required folder structure with purposes
- `note_types` - Defined note types with properties and templates
- `linking` - Linking conventions and patterns
- `tags` - Tagging strategy and conventions
- `workflow` - Recommended workflows and processes
- `principles` - Core philosophical principles (optional)
- `best_practices` - Guidelines for effective use (optional)

### Validation Example

```python
# Plugin can validate vault against methodology
methodology = load_methodology("lyt-ace")
results = validate_vault(vault_path, methodology)

# Results include:
# - Missing required folders
# - Notes in wrong locations
# - Missing required properties
# - Linking pattern violations
# - Suggestions for improvement
```

---

## Extending Methodologies

### Creating a Custom Methodology

1. Copy an existing methodology YAML file
2. Modify the structure to match your needs
3. Save with a descriptive name
4. Test validation against your vault

### Mixing Methodologies

Some users successfully combine aspects of multiple methodologies:

- **PARA + Zettelkasten** - PARA for active work, Zettelkasten for knowledge
- **LYT + PARA** - LYT navigation with PARA's actionability
- **Minimal + Daily Notes** - Simple structure with temporal anchoring

---

## Resources

### LYT-ACE
- [Linking Your Thinking](https://www.linkingyourthinking.com)
- [LYT Workshop](https://www.linkingyourthinking.com/lyt-workshop)

### PARA
- [The PARA Method](https://fortelabs.com/blog/para/)
- [Building a Second Brain](https://www.buildingasecondbrain.com)

### Zettelkasten
- [Zettelkasten.de Introduction](https://zettelkasten.de/introduction/)
- [How to Take Smart Notes](https://takesmartnotes.com) (Sönke Ahrens)

### Minimal
- [File Over App](https://stephanango.com/file-over-app)
- [Obsidian Minimal Theme](https://minimal.guide)

---

## Contributing

To contribute a new methodology configuration:

1. Create a new YAML file in this directory
2. Follow the structure of existing methodologies
3. Include comprehensive documentation in the YAML
4. Update this README with a description
5. Submit a pull request

---

*Last updated: 2025-12-23*
