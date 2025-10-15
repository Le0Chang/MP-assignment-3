Please create a visually striking, single-page personal portfolio website for me. The design should be inspired by the "digital rain" effect from the movie The Matrix, but with a unique color theme.

# My Information:

- Name: Zhiming Chang (Leo)

- Bio: I'm currently a graduate student at Johns Hopkins University, focusing on optimization and machine learning. My research interests include the intersection of Software Engineering and Artificial Intelligence and Multimodal Large Language Models. I enjoy programming and playing sports.

# Core Visual Requirements:

1. Theme: 
The website must have a dark, professional theme inspired by Johns Hopkins University's colors. The background should be a deep "Hopkins Blue" (#002D72).

2. Animated Background: 
The most important feature is a full-screen, animated background using an HTML <canvas> element. This animation should recreate the "Matrix digital rain" effect, but instead of green, the falling characters should be a lighter "Spirit Blue" (#68ACE5) or white to contrast with the dark blue background.

3. Typography: 
All primary text (name, bio, links) should be white or a very light grey to ensure excellent readability against the deep blue background.

# Content and Layout:
All content should be centered horizontally and vertically on the page.

1. Header:

- Display my name, "Zhiming Chang".

- Below my name, add the title: "Applied Mathematics and Statistics | Master".

- Apply a subtle "typewriter" or digital "glitch" effect so this text animates on page load.

2. Content Sections and Interactivity:

- Navigation: Create a menu with four links: "About Me", "Updates", "Experience", and "Contact".

    - Hover Effect: When a user hovers over a navigation link, its background must change to a solid, light blue (#68ACE5), and the text color must change to the deep blue background color (#002D72).

- Content Display: The page must contain four distinct content sections, one for each navigation link.

    - The "About Me" section should contain the bio text from above.

    - The "Updates" section should display my recent research focus: "starting researching on Specification Generation".

    - The "Experience" section should list my educational background:

        - 2021-2025: Shandong University, Statistics (Data Science and Artificial Intelligence Experimental Class)

        - 2025-Present: Johns Hopkins University, MSE AMS

    - The "Contact" section should contain my social links:

        - GitHub: https://github.com/Le0Chang

        - Email: zchang9@jh.edu or changzhiming622@gmail.com

        - Please use appropriate icons for these links.

- Click Interaction: Implement JavaScript functionality for single-page navigation:

    - When the page first loads, only the "About Me" section should be visible.

    - When a user clicks a navigation link (e.g., "Experience"), hide all other content sections and display only the corresponding "Experience" section.

# Technical and Testing Requirements:

- The entire website must be a single, self-contained index.html file. All CSS and JavaScript (including the canvas animation script) must be embedded within this one file.

- This is a static website, so no API tests are necessary.

- After you have created the index.html file, please run the existing UI tests located at tests/ui.test.js to verify that the basic page structure is correct.