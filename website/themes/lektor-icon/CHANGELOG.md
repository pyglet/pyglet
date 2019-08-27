# Lektor-Icon Changelog


## 2019-02-01

Feature additions:

- Spyder blog module to theme and unify with existing templates
- A generic page template/model with basic styling
- A 404 error page template/model
- A working, all new "mission" flowblock for the mainpage, and many fixes to others
- Numerous new automatic/configurable features to individual flowblocks
- A fully configurable footer with multiple sections
- Optional integrations with Gitter, OpenCollective, Disqus comments, Atom/RSS feeds, video streaming sites and more
- A configurable CSP and many other privacy and security improvements

User-visible enhancements:

- Refactor title, logo, and other elements hardcoded to Spyder-specific values to make theme actually usable on other sites
- Rework single-page model/template to allow for a far more flexible and customizable layout with dynamic alternating background color
- Make navigation bar display properly and automatically add section and page links
- Make images responsive for faster loading and better quality
- Add support for setting an overall theme/accent color in theme settings
- Overhaul all layouts for much greater responsiveness across viewport sizes
- Handle null various for essentially every setting so site degrades gracefully
- Move most settings from theme to models for admin panel configuration and avoid breaking rebuilds
- Add labels, descriptions, etc. to all model properties for easier configuration
- Port over custom styles so site looks good out of the box
- Refine design, add new styling cues and address accessibility issues
- Fix dozens of layout bugs and issues

Techdebt, refactoring and maintainability:

- Unify existing models and template to remove large amount of duplication
- Update theme, HTML, CSS, JS and HTTP headers to current standards
- Expand Readme and add contributing guide for easier development
- Add proper authors, licensing, third party notice information and other meta-files
- Add images/, example site and other elements for inclusion in the Lektor themes repo and gallery
- Refactor file, model/flowblock, class/id and property/option names for consistency and clarity
- Factor out or remove no longer needed CSS, JS and fonts
- Update vendored code (JQuery and friends) to modern, secure versions
- Conform project to a suite of consistent best practices and conventions
- Minify stylesheets and JS libraries


## 2018-02-20

- Port the theme to Lektor (@dalthviz)


## 2017-11-14

- Contact links were fixed [https://github.com/SteveLane/hugo-icon/issues/3](https://github.com/SteveLane/hugo-icon/issues/3) (@MartinWillitts)
- Slight change to original main.js
- A linkedin option was added to configuration (@MartinWillitts)


## 2017-09-21

- Theme ported to Hugo with no changes made to styling/theming
- Adjusted contact form to work with netlify
