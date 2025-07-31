import os
import re
import yaml
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional
from pocketflow import Node, BatchNode
from file_operations.repository_scanner import scan_github_repository
from ai_interface.model_connector import query_language_model
from file_operations.filesystem_explorer import explore_local_directory

def extract_file_content_by_indices(file_collection: List[Tuple[str, str]], target_indices: List[int]) -> Dict[str, str]:
    content_mapping = {}
    for index in target_indices:
        if 0 <= index < len(file_collection):
            file_path, file_content = file_collection[index]
            content_mapping[f"{index} # {file_path}"] = file_content
    return content_mapping

class CodebaseRetriever(Node):
    def prep(self, workspace_config):
        repository_url = workspace_config.get("source_repository")
        local_path = workspace_config.get("local_filesystem_path")
        project_name = workspace_config.get("project_identifier")
        
        if not project_name:
            if repository_url:
                project_name = repository_url.split("/")[-1].replace(".git", "")
            else:
                project_name = os.path.basename(os.path.abspath(local_path))
            workspace_config["project_identifier"] = project_name
            
        file_inclusion_patterns = workspace_config["included_file_patterns"]
        file_exclusion_patterns = workspace_config["excluded_file_patterns"]
        size_limit_bytes = workspace_config["maximum_file_size_bytes"]
        
        return {
            "repository_url": repository_url,
            "local_directory": local_path,
            "api_token": workspace_config.get("github_api_token"),
            "inclusion_patterns": file_inclusion_patterns,
            "exclusion_patterns": file_exclusion_patterns,
            "file_size_limit": size_limit_bytes,
            "use_relative_paths": True,
        }
        
    def exec(self, preparation_result):
        if preparation_result["repository_url"]:
            print(f"Scanning remote repository: {preparation_result['repository_url']}...")
            scan_results = scan_github_repository(
                repo_url=preparation_result["repository_url"],
                token=preparation_result["api_token"],
                include_patterns=preparation_result["inclusion_patterns"],
                exclude_patterns=preparation_result["exclusion_patterns"],
                max_file_size=preparation_result["file_size_limit"],
                use_relative_paths=preparation_result["use_relative_paths"],
            )
        else:
            print(f"Exploring local directory: {preparation_result['local_directory']}...")
            scan_results = explore_local_directory(
                directory=preparation_result["local_directory"],
                include_patterns=preparation_result["inclusion_patterns"],
                exclude_patterns=preparation_result["exclusion_patterns"],
                max_file_size=preparation_result["file_size_limit"],
                use_relative_paths=preparation_result["use_relative_paths"]
            )
            
        discovered_files = list(scan_results.get("files", {}).items())
        if not discovered_files:
            raise ValueError("No files were successfully retrieved from the source")
        print(f"Successfully retrieved {len(discovered_files)} files.")
        return discovered_files
        
    def post(self, workspace_config, preparation_result, execution_result):
        workspace_config["discovered_files"] = execution_result

class ConceptIdentifier(Node):
    def prep(self, workspace_config):
        file_collection = workspace_config["discovered_files"]
        project_name = workspace_config["project_identifier"]
        target_language = workspace_config.get("target_language", "english")
        caching_enabled = workspace_config.get("enable_ai_caching", True)
        max_concepts = workspace_config.get("maximum_concept_count", 10)
        
        def build_analysis_context(files_data):
            full_context = ""
            file_metadata = []
            for index, (path, content) in enumerate(files_data):
                context_entry = f"--- File Index {index}: {path} ---\n{content}\n\n"
                full_context += context_entry
                file_metadata.append((index, path))
            return full_context, file_metadata
            
        analysis_context, file_metadata = build_analysis_context(file_collection)
        file_listing_text = "\n".join([f"- {idx} # {path}" for idx, path in file_metadata])
        
        return (
            analysis_context, file_listing_text, len(file_collection),
            project_name, target_language, caching_enabled, max_concepts
        )
        
    def exec(self, preparation_result):
        (context, file_listing, file_count, project_name, 
         language, use_cache, max_concepts) = preparation_result
        
        print(f"Identifying core concepts using AI analysis...")
        
        language_directive = ""
        name_language_note = ""
        description_language_note = ""
        
        if language.lower() != "english":
            language_directive = f"CRITICAL: Generate concept `name` and `description` fields in **{language.capitalize()}** language exclusively. Avoid English for these fields.\n\n"
            name_language_note = f" (must be in {language.capitalize()})"
            description_language_note = f" (must be in {language.capitalize()})"
            
        analysis_prompt = f"""
For the software project `{project_name}`:

Source Code Analysis Context:
{context}

{language_directive}Examine the provided codebase thoroughly.
Identify the 5-{max_concepts} most crucial architectural concepts that newcomers should understand.

For each concept, specify:
1. A clear `name`{name_language_note}.
2. A beginner-friendly `description` explaining the concept with simple analogies, approximately 100 words{description_language_note}.
3. A list of relevant `file_indices` (integers) using format `idx # path/comment`.

Available file indices and paths:
{file_listing}

Structure the response as YAML:

```yaml
- name: |
    Data Processing{name_language_note}
  description: |
    Describes the concept's purpose and functionality.
    Acts like a central hub managing data flow.{description_language_note}
  file_indices:
    - 0 # path/to/core.py
    - 3 # path/to/helper.py
- name: |
    User Interface{name_language_note}
  description: |
    Another essential concept, similar to a blueprint for interactions.{description_language_note}
  file_indices:
    - 5 # path/to/interface.js
```"""

        ai_response = query_language_model(analysis_prompt, use_cache=(use_cache and self.cur_retry == 0))
        
        yaml_content = ai_response.strip().split("```yaml")[1].split("```")[0].strip()
        parsed_concepts = yaml.safe_load(yaml_content)
        
        if not isinstance(parsed_concepts, list):
            raise ValueError("AI response format is invalid - expected list structure")
            
        validated_concepts = []
        for concept_item in parsed_concepts:
            required_fields = ["name", "description", "file_indices"]
            if not isinstance(concept_item, dict) or not all(field in concept_item for field in required_fields):
                raise ValueError(f"Concept missing required fields: {concept_item}")
                
            if not all(isinstance(concept_item[field], str) for field in ["name", "description"]):
                raise ValueError(f"Name and description must be strings: {concept_item}")
                
            if not isinstance(concept_item["file_indices"], list):
                raise ValueError(f"File indices must be a list: {concept_item}")
                
            processed_indices = []
            for index_entry in concept_item["file_indices"]:
                try:
                    if isinstance(index_entry, int):
                        file_index = index_entry
                    elif isinstance(index_entry, str) and "#" in index_entry:
                        file_index = int(index_entry.split("#")[0].strip())
                    else:
                        file_index = int(str(index_entry).strip())
                        
                    if not (0 <= file_index < file_count):
                        raise ValueError(f"File index {file_index} out of range for concept {concept_item['name']}")
                    processed_indices.append(file_index)
                except (ValueError, TypeError):
                    raise ValueError(f"Cannot parse index entry: {index_entry} in concept {concept_item['name']}")
                    
            concept_item["files"] = sorted(list(set(processed_indices)))
            validated_concepts.append({
                "name": concept_item["name"],
                "description": concept_item["description"],
                "files": concept_item["files"],
            })
            
        print(f"Successfully identified {len(validated_concepts)} core concepts.")
        print(f"📚 Will generate {len(validated_concepts)} tutorial chapters")
        return validated_concepts
        
    def post(self, workspace_config, preparation_result, execution_result):
        workspace_config["identified_concepts"] = execution_result

class RelationshipAnalyzer(Node):
    def prep(self, workspace_config):
        concepts_data = workspace_config["identified_concepts"]
        file_collection = workspace_config["discovered_files"]
        project_name = workspace_config["project_identifier"]
        target_language = workspace_config.get("target_language", "english")
        caching_enabled = workspace_config.get("enable_ai_caching", True)
        
        concepts_count = len(concepts_data)
        
        analysis_context = "Identified Core Concepts:\n"
        all_referenced_indices = set()
        concept_descriptions = []
        
        for index, concept in enumerate(concepts_data):
            file_indices_text = ", ".join(map(str, concept["files"]))
            concept_summary = f"- Index {index}: {concept['name']} (Related files: [{file_indices_text}])\n  Description: {concept['description']}"
            analysis_context += concept_summary + "\n"
            concept_descriptions.append(f"{index} # {concept['name']}")
            all_referenced_indices.update(concept["files"])
            
        analysis_context += "\nRelevant Source Code (Indexed by File):\n"
        relevant_file_content = extract_file_content_by_indices(
            file_collection, sorted(list(all_referenced_indices))
        )
        
        file_context_section = "\n\n".join(
            f"--- File: {index_path} ---\n{content}"
            for index_path, content in relevant_file_content.items()
        )
        analysis_context += file_context_section
        
        return (
            analysis_context, "\n".join(concept_descriptions), concepts_count,
            project_name, target_language, caching_enabled
        )
        
    def exec(self, preparation_result):
        (context, concept_listing, concepts_count, project_name, language, use_cache) = preparation_result
        
        print(f"Analyzing concept relationships using AI...")
        
        language_directive = ""
        language_hint = ""
        input_language_note = ""
        
        if language.lower() != "english":
            language_directive = f"IMPORTANT: Generate `summary` and relationship `label` fields in **{language.capitalize()}** language exclusively. Do not use English for these fields.\n\n"
            language_hint = f" (in {language.capitalize()})"
            input_language_note = f" (Concept names might be in {language.capitalize()})"
            
        relationship_prompt = f"""
Analyze the following architectural concepts and source code from project `{project_name}`:

Concept Index and Names{input_language_note}:
{concept_listing}

Detailed Context (Concepts, Descriptions, Source Code):
{context}

{language_directive}Please provide:
1. A comprehensive `summary` describing the project's primary purpose and key functionality in beginner-friendly language{language_hint}. Use markdown formatting with **bold** and *italic* emphasis for important terms.
2. A collection (`relationships`) documenting significant interactions between concepts. For each relationship, include:
    - `from_abstraction`: Source concept index (e.g., `0 # ConceptName1`)
    - `to_abstraction`: Target concept index (e.g., `1 # ConceptName2`)
    - `label`: Brief interaction description **in just a few words**{language_hint} (e.g., "Controls", "Extends", "Utilizes").
    Focus on relationships backed by actual code dependencies or data flow.
    Simplify and prioritize the most important relationships.

CRITICAL: Ensure EVERY concept appears in at least ONE relationship (as either source or target). All concept indices must be represented.

Format as YAML:

```yaml
summary: |
  Clear, accessible project explanation{language_hint}.
  Multiple lines allowed with **bold** and *italic* formatting.
relationships:
  - from_abstraction: 0 # ConceptName1
    to_abstraction: 1 # ConceptName2
    label: "Controls"{language_hint}
  - from_abstraction: 2 # ConceptName3
    to_abstraction: 0 # ConceptName1
    label: "Supplies data"{language_hint}
```

Provide the YAML response:
"""

        ai_response = query_language_model(relationship_prompt, use_cache=(use_cache and self.cur_retry == 0))
        
        yaml_content = ai_response.strip().split("```yaml")[1].split("```")[0].strip()
        relationship_data = yaml.safe_load(yaml_content)
        
        required_keys = ["summary", "relationships"]
        if not isinstance(relationship_data, dict) or not all(key in relationship_data for key in required_keys):
            raise ValueError("AI response missing required keys ('summary', 'relationships')")
            
        if not isinstance(relationship_data["summary"], str):
            raise ValueError("Summary field must be a string")
        if not isinstance(relationship_data["relationships"], list):
            raise ValueError("Relationships field must be a list")
            
        validated_relationships = []
        for relationship in relationship_data["relationships"]:
            required_rel_fields = ["from_abstraction", "to_abstraction", "label"]
            if not isinstance(relationship, dict) or not all(field in relationship for field in required_rel_fields):
                raise ValueError(f"Relationship missing required fields: {relationship}")
                
            if not isinstance(relationship["label"], str):
                raise ValueError(f"Relationship label must be string: {relationship}")
                
            try:
                from_index = int(str(relationship["from_abstraction"]).split("#")[0].strip())
                to_index = int(str(relationship["to_abstraction"]).split("#")[0].strip())
                
                if not (0 <= from_index < concepts_count and 0 <= to_index < concepts_count):
                    raise ValueError(f"Invalid relationship indices: from={from_index}, to={to_index}")
                    
                validated_relationships.append({
                    "from": from_index,
                    "to": to_index,
                    "label": relationship["label"],
                })
            except (ValueError, TypeError):
                raise ValueError(f"Cannot parse relationship indices: {relationship}")
                
        print("Successfully analyzed project structure and concept relationships.")
        return {
            "summary": relationship_data["summary"],
            "details": validated_relationships,
        }
        
    def post(self, workspace_config, preparation_result, execution_result):
        workspace_config["concept_relationships"] = execution_result

class ChapterOrganizer(Node):
    def prep(self, workspace_config):
        concepts_data = workspace_config["identified_concepts"]
        relationships_data = workspace_config["concept_relationships"]
        project_name = workspace_config["project_identifier"]
        target_language = workspace_config.get("target_language", "english")
        caching_enabled = workspace_config.get("enable_ai_caching", True)
        
        concept_descriptions = []
        for index, concept in enumerate(concepts_data):
            concept_descriptions.append(f"- {index} # {concept['name']}")
        concept_listing = "\n".join(concept_descriptions)
        
        language_note = ""
        if target_language.lower() != "english":
            language_note = f" (Note: Project summary might be in {target_language.capitalize()})"
            
        context_description = f"Project Overview{language_note}:\n{relationships_data['summary']}\n\n"
        context_description += "Concept Relationships (Indices reference concepts above):\n"
        
        for relationship in relationships_data["details"]:
            from_concept_name = concepts_data[relationship["from"]]["name"]
            to_concept_name = concepts_data[relationship["to"]]["name"]
            context_description += f"- From {relationship['from']} ({from_concept_name}) to {relationship['to']} ({to_concept_name}): {relationship['label']}\n"
            
        input_language_note = ""
        if target_language.lower() != "english":
            input_language_note = f" (Names might be in {target_language.capitalize()})"
            
        return (
            concept_listing, context_description, len(concepts_data),
            project_name, input_language_note, caching_enabled
        )
        
    def exec(self, preparation_result):
        (concept_listing, context, concepts_count, project_name, language_note, use_cache) = preparation_result
        
        print("Determining optimal chapter sequence using AI...")
        
        ordering_prompt = f"""
Given these architectural concepts and their relationships for project `{project_name}`:

Available Concepts (Index # Name){language_note}:
{concept_listing}

Project context including relationships and overview:
{context}

For creating an effective tutorial about `{project_name}`, determine the optimal sequence for explaining these concepts.
Start with foundational or user-facing concepts that provide entry points, then progress to detailed implementation specifics or supporting elements.

Return the ordered concept indices with names for clarity, using format `idx # ConceptName`.

```yaml
- 2 # FoundationalElement
- 0 # CoreComponentA
- 1 # CoreComponentB (depends on CoreComponentA)
- ...
```

Provide the YAML sequence:
"""

        ai_response = query_language_model(ordering_prompt, use_cache=(use_cache and self.cur_retry == 0))
        
        yaml_content = ai_response.strip().split("```yaml")[1].split("```")[0].strip()
        ordered_sequence = yaml.safe_load(yaml_content)
        
        if not isinstance(ordered_sequence, list):
            raise ValueError("AI response must be a list of ordered indices")
            
        processed_sequence = []
        seen_indices = set()
        
        for sequence_entry in ordered_sequence:
            try:
                if isinstance(sequence_entry, int):
                    concept_index = sequence_entry
                elif isinstance(sequence_entry, str) and "#" in sequence_entry:
                    concept_index = int(sequence_entry.split("#")[0].strip())
                else:
                    concept_index = int(str(sequence_entry).strip())
                    
                if not (0 <= concept_index < concepts_count):
                    raise ValueError(f"Index {concept_index} out of valid range")
                if concept_index in seen_indices:
                    raise ValueError(f"Duplicate index {concept_index} in sequence")
                    
                processed_sequence.append(concept_index)
                seen_indices.add(concept_index)
                
            except (ValueError, TypeError):
                raise ValueError(f"Cannot parse sequence entry: {sequence_entry}")
                
        if len(processed_sequence) != concepts_count:
            missing_indices = set(range(concepts_count)) - seen_indices
            raise ValueError(f"Sequence length mismatch. Missing indices: {missing_indices}")
            
        print(f"Determined chapter sequence (indices): {processed_sequence}")
        print(f"📖 Chapter generation order: {len(processed_sequence)} chapters total")
        return processed_sequence
        
    def post(self, workspace_config, preparation_result, execution_result):
        workspace_config["chapter_sequence"] = execution_result

class ContentGenerator(BatchNode):
    def prep(self, workspace_config):
        chapter_sequence = workspace_config["chapter_sequence"]
        concepts_data = workspace_config["identified_concepts"]
        file_collection = workspace_config["discovered_files"]
        project_name = workspace_config["project_identifier"]
        target_language = workspace_config.get("target_language", "english")
        caching_enabled = workspace_config.get("enable_ai_caching", True)
        
        self.completed_chapters = []
        
        all_chapter_entries = []
        chapter_metadata = {}
        
        for position, concept_index in enumerate(chapter_sequence):
            if 0 <= concept_index < len(concepts_data):
                chapter_number = position + 1
                concept_name = concepts_data[concept_index]["name"]
                sanitized_filename = "".join(c if c.isalnum() else "_" for c in concept_name).lower()
                chapter_filename = f"{chapter_number:02d}_{sanitized_filename}.md"
                
                all_chapter_entries.append(f"{chapter_number}. [{concept_name}]({chapter_filename})")
                chapter_metadata[concept_index] = {
                    "num": chapter_number,
                    "name": concept_name,
                    "filename": chapter_filename,
                }
                
        complete_chapter_index = "\n".join(all_chapter_entries)
        
        processing_items = []
        for position, concept_index in enumerate(chapter_sequence):
            if 0 <= concept_index < len(concepts_data):
                concept_details = concepts_data[concept_index]
                related_file_indices = concept_details.get("files", [])
                related_file_content = extract_file_content_by_indices(file_collection, related_file_indices)
                
                previous_chapter_info = None
                if position > 0:
                    prev_index = chapter_sequence[position - 1]
                    previous_chapter_info = chapter_metadata[prev_index]
                    
                next_chapter_info = None
                if position < len(chapter_sequence) - 1:
                    next_index = chapter_sequence[position + 1]
                    next_chapter_info = chapter_metadata[next_index]
                    
                processing_items.append({
                    "chapter_number": position + 1,
                    "concept_index": concept_index,
                    "concept_details": concept_details,
                    "related_file_content": related_file_content,
                    "project_name": project_name,
                    "complete_chapter_index": complete_chapter_index,
                    "chapter_metadata": chapter_metadata,
                    "previous_chapter_info": previous_chapter_info,
                    "next_chapter_info": next_chapter_info,
                    "target_language": target_language,
                    "caching_enabled": caching_enabled,
                })
            else:
                print(f"Warning: Invalid concept index {concept_index} in sequence. Skipping.")
                
        print(f"Preparing to generate {len(processing_items)} tutorial chapters...")
        print(f"📝 Starting batch chapter generation for {len(processing_items)} chapters...")
        return processing_items
        
    def exec(self, chapter_item):
        concept_name = chapter_item["concept_details"]["name"]
        concept_description = chapter_item["concept_details"]["description"]
        chapter_number = chapter_item["chapter_number"]
        project_name = chapter_item.get("project_name")
        target_language = chapter_item.get("target_language", "english")
        caching_enabled = chapter_item.get("caching_enabled", True)
        
        print(f"Generating chapter {chapter_number} for concept: {concept_name} using AI...")
        print(f"⏳ Progress: Chapter {chapter_number} of {len(self.completed_chapters) + len(chapter_item['chapter_metadata'])} chapters")
        
        file_context_section = "\n\n".join(
            f"--- File: {index_path.split('# ')[1] if '# ' in index_path else index_path} ---\n{content}"
            for index_path, content in chapter_item["related_file_content"].items()
        )
        
        previous_chapters_context = "\n---\n".join(self.completed_chapters)
        
        language_directive = ""
        concept_language_note = ""
        structure_language_note = ""
        previous_context_note = ""
        instruction_language_note = ""
        diagram_language_note = ""
        comment_language_note = ""
        link_language_note = ""
        tone_language_note = ""
        
        if target_language.lower() != "english":
            lang_cap = target_language.capitalize()
            language_directive = f"CRITICAL: Write this COMPLETE tutorial chapter in **{lang_cap}**. Input context (concept name, description, chapter list, previous content) might be in {lang_cap}, but you MUST translate ALL generated content including explanations, examples, technical terminology, and code comments into {lang_cap}. Use English ONLY for code syntax, proper nouns, or when explicitly specified. The entire output MUST be in {lang_cap}.\n\n"
            concept_language_note = f" (Note: Provided in {lang_cap})"
            structure_language_note = f" (Note: Chapter names might be in {lang_cap})"
            previous_context_note = f" (Note: This content might be in {lang_cap})"
            instruction_language_note = f" (in {lang_cap})"
            diagram_language_note = f" (Use {lang_cap} for labels/text where appropriate)"
            comment_language_note = f" (Translate to {lang_cap} when possible, keep minimal English for clarity)"
            link_language_note = f" (Use the {lang_cap} chapter title from structure above)"
            tone_language_note = f" (appropriate for {lang_cap} readers)"
            
        chapter_generation_prompt = f"""
{language_directive}Create a comprehensive, beginner-friendly tutorial chapter (in Markdown format) for project `{project_name}` about the concept: "{concept_name}". This is Chapter {chapter_number}.

Concept Information{concept_language_note}:
- Name: {concept_name}
- Description:
{concept_description}

Full Tutorial Structure{structure_language_note}:
{chapter_item["complete_chapter_index"]}

Previous Chapters Context{previous_context_note}:
{previous_chapters_context if previous_chapters_context else "This is the first chapter."}

Relevant Source Code (Code syntax unchanged):
{file_context_section if file_context_section else "No specific code examples provided for this concept."}

Chapter Generation Guidelines (Generate all content in {target_language.capitalize()} unless specified otherwise):
- Begin with clear heading (e.g., `# Chapter {chapter_number}: {concept_name}`). Use the provided concept name.

- If not the first chapter, start with smooth transition from previous chapter{instruction_language_note}, referencing it with proper Markdown link using its name{link_language_note}.

- Start with high-level motivation explaining what problem this concept solves{instruction_language_note}. Begin with a concrete use case example. Guide the reader to understand how to solve this use case. Keep it minimal and beginner-friendly.

- For complex concepts, break down into key sub-concepts. Explain each sub-concept individually in very beginner-friendly manner{instruction_language_note}.

- Explain how to use this concept to solve the use case{instruction_language_note}. Provide example inputs and outputs for code snippets (if output isn't values, describe at high level what happens{instruction_language_note}).

- Keep each code block BELOW 10 lines! For longer code blocks, break them into smaller pieces and walk through them individually. Aggressively simplify code to make it minimal. Use comments{comment_language_note} to skip non-important implementation details. Each code block should have beginner-friendly explanation immediately after{instruction_language_note}.

- Describe internal implementation to help understand what's under the hood{instruction_language_note}. First provide non-code or code-light walkthrough of what happens step-by-step when concept is used{instruction_language_note}. Recommend simple sequenceDiagram with dummy example - keep minimal with at most 5 participants for clarity. If participant name has space, use: `participant QP as Query Processing`. {diagram_language_note}.

- Then dive deeper into code for internal implementation with file references. Provide example code blocks, but keep them simple and beginner-friendly. Explain thoroughly{instruction_language_note}.

- IMPORTANT: When referencing other core concepts covered in other chapters, ALWAYS use proper Markdown links like: [Chapter Title](filename.md). Use the Full Tutorial Structure above to find correct filename and chapter title{link_language_note}. Translate surrounding text.

- Use mermaid diagrams to illustrate complex concepts (```mermaid``` format). {diagram_language_note}.

- Extensively use analogies and examples throughout{instruction_language_note} to help beginners understand.

- End chapter with brief conclusion summarizing what was learned{instruction_language_note} and providing transition to next chapter{instruction_language_note}. If there is a next chapter, use proper Markdown link: [Next Chapter Title](next_chapter_filename){link_language_note}.

- Ensure tone is welcoming and accessible for newcomers{tone_language_note}.

- Output *only* the Markdown content for this chapter.

Provide the comprehensive, beginner-friendly Markdown output (DON'T include ```markdown``` tags):
"""

        chapter_content = query_language_model(chapter_generation_prompt, use_cache=(caching_enabled and self.cur_retry == 0))
        
        expected_heading = f"# Chapter {chapter_number}: {concept_name}"
        if not chapter_content.strip().startswith(f"# Chapter {chapter_number}"):
            content_lines = chapter_content.strip().split("\n")
            if content_lines and content_lines[0].strip().startswith("#"):
                content_lines[0] = expected_heading
                chapter_content = "\n".join(content_lines)
            else:
                chapter_content = f"{expected_heading}\n\n{chapter_content}"
                
        self.completed_chapters.append(chapter_content)
        return chapter_content
        
    def post(self, workspace_config, preparation_result, execution_result_list):
        workspace_config["generated_chapters"] = execution_result_list
        del self.completed_chapters
        print(f"Successfully generated {len(execution_result_list)} tutorial chapters.")
        print(f"✅ Chapter generation complete: {len(execution_result_list)} chapters ready for assembly")

class DocumentationAssembler(Node):
    def prep(self, workspace_config):
        project_name = workspace_config["project_identifier"]
        output_directory = workspace_config.get("documentation_output_path", "output")
        final_output_path = os.path.join(output_directory, project_name)
        repository_url = workspace_config.get("source_repository")
        
        relationships_data = workspace_config["concept_relationships"]
        chapter_sequence = workspace_config["chapter_sequence"]
        concepts_data = workspace_config["identified_concepts"]
        chapter_contents = workspace_config["generated_chapters"]
        
        diagram_lines = ["flowchart TD"]
        
        for index, concept in enumerate(concepts_data):
            node_identifier = f"A{index}"
            sanitized_concept_name = concept["name"].replace('"', "")
            node_label = sanitized_concept_name
            diagram_lines.append(f'    {node_identifier}["{node_label}"]')
            
        for relationship in relationships_data["details"]:
            from_node_id = f"A{relationship['from']}"
            to_node_id = f"A{relationship['to']}"
            edge_label = relationship["label"].replace('"', "").replace("\n", " ")
            max_label_length = 30
            if len(edge_label) > max_label_length:
                edge_label = edge_label[:max_label_length - 3] + "..."
            diagram_lines.append(f'    {from_node_id} -- "{edge_label}" --> {to_node_id}')
            
        mermaid_diagram = "\n".join(diagram_lines)
        
        index_content = f"# Tutorial: {project_name}\n\n"
        index_content += f"{relationships_data['summary']}\n\n"
        index_content += f"**Source Repository:** [{repository_url}]({repository_url})\n\n"
        
        index_content += "```mermaid\n"
        index_content += mermaid_diagram + "\n"
        index_content += "```\n\n"
        
        index_content += f"## Chapters\n\n"
        
        chapter_file_list = []
        
        for position, concept_index in enumerate(chapter_sequence):
            if 0 <= concept_index < len(concepts_data) and position < len(chapter_contents):
                concept_name = concepts_data[concept_index]["name"]
                sanitized_name = "".join(c if c.isalnum() else "_" for c in concept_name).lower()
                chapter_filename = f"{position+1:02d}_{sanitized_name}.md"
                index_content += f"{position+1}. [{concept_name}]({chapter_filename})\n"
                
                chapter_content = chapter_contents[position]
                if not chapter_content.endswith("\n\n"):
                    chapter_content += "\n\n"
                chapter_content += f"---\n\nGenerated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)"
                
                chapter_file_list.append({"filename": chapter_filename, "content": chapter_content})
            else:
                print(f"Warning: Mismatch between sequence, concepts, or content at position {position}. Skipping file generation.")
                
        index_content += f"\n\n---\n\nGenerated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)"
        
        return {
            "final_output_path": final_output_path,
            "index_content": index_content,
            "chapter_files": chapter_file_list,
        }
        
    def exec(self, preparation_result):
        output_path = preparation_result["final_output_path"]
        index_content = preparation_result["index_content"]
        chapter_files = preparation_result["chapter_files"]
        
        print(f"Assembling final documentation in directory: {output_path}")
        os.makedirs(output_path, exist_ok=True)
        
        index_file_path = os.path.join(output_path, "index.md")
        with open(index_file_path, "w", encoding="utf-8") as index_file:
            index_file.write(index_content)
        print(f"  - Created {index_file_path}")
        
        for chapter_info in chapter_files:
            chapter_file_path = os.path.join(output_path, chapter_info["filename"])
            with open(chapter_file_path, "w", encoding="utf-8") as chapter_file:
                chapter_file.write(chapter_info["content"])
            print(f"  - Created {chapter_file_path}")
            
        return output_path
        
    def post(self, workspace_config, preparation_result, execution_result):
        workspace_config["final_documentation_path"] = execution_result
        print(f"\nDocumentation generation completed! Files available at: {execution_result}")
