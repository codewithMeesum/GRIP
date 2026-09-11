import os, json
import streamlit as st
from database import init_db, seed_demo_data, create_report, list_reports, get_report, add_comment, list_comments, update_status
from ai_service import analyze_environmental_report, generate_green_innovation

st.set_page_config(page_title='GRIP — Green Reporting & Innovation Platform', page_icon='🌱', layout='wide')

st.markdown('''<style>
.block-container{max-width:1220px;padding-top:1.5rem}.hero{padding:1.4rem 1.5rem;border:1px solid #dce7df;border-radius:22px;background:linear-gradient(135deg,#eff8f1,#fff 55%,#f7fbf8)}.brand{font-weight:800;font-size:2.5rem;color:#10221a;letter-spacing:-.04em}.tagline{color:#617269}.pill,.status{display:inline-block;padding:.28rem .65rem;border-radius:999px;font-size:.78rem;font-weight:700}.pill{background:#e8f5ed;color:#14683f;border:1px solid #cfe6d7}.status{background:#f0f5f1;border:1px solid #dce7df}.card{border:1px solid #dce7df;border-radius:18px;padding:1rem 1.1rem;background:#fff;margin-bottom:.8rem}.small{color:#617269;font-size:.88rem}.metric{border:1px solid #dce7df;border-radius:16px;padding:.85rem 1rem}.metric-num{font-size:1.65rem;font-weight:800}.metric-label{color:#617269;font-size:.82rem}
</style>''', unsafe_allow_html=True)
init_db(); seed_demo_data()

def badge(s): return f'<span class="status">{s}</span>'

def render_card(r):
    st.markdown('<div class="card">', unsafe_allow_html=True)
    a,b=st.columns([4,1])
    with a:
        st.markdown(f'### {r["title"]}')
        st.markdown(f'<span class="pill">{r["category"]}</span>&nbsp;{badge(r["status"])}', unsafe_allow_html=True)
        st.markdown(f'<div class="small">📍 {r["location"]} · {r["created_at"]}</div>', unsafe_allow_html=True)
        st.write(r['description'])
    with b:
        if st.button('Open', key=f'open_{r["id"]}', use_container_width=True):
            st.session_state.selected_report=r['id']; st.session_state.page='Issue'; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown('## 🌱 GRIP')
    st.caption('Green Reporting & Innovation Platform')
    page=st.radio('Navigate',['Home','Report an Issue','Innovation Lab','Dashboard'], index=['Home','Report an Issue','Innovation Lab','Dashboard'].index(st.session_state.get('page','Home')))
    st.session_state.page=page
    st.divider(); st.caption('Hackathon MVP'); st.write('Report → Analyze → Discuss → Track → Innovate')

if st.session_state.page=='Home':
    st.markdown('<div class="hero"><div class="brand">GRIP</div><div class="tagline">Green Reporting & Innovation Platform</div><p style="margin-top:.8rem;color:#2d4338">A community-driven platform that turns environmental problems into structured, AI-assisted cases and practical green innovation opportunities.</p></div>', unsafe_allow_html=True)
    reports=list_reports(); total=len(reports); verified=sum(r['status']=='Verified' for r in reports); action=sum(r['status']=='Action Required' for r in reports); resolved=sum(r['status']=='Resolved' for r in reports)
    st.write(''); cols=st.columns(4)
    for c,v,l in zip(cols,[total,verified,action,resolved],['Total Reports','Verified','Action Required','Resolved']):
        c.markdown(f'<div class="metric"><div class="metric-num">{v}</div><div class="metric-label">{l}</div></div>',unsafe_allow_html=True)
    st.write(''); st.subheader('Latest environmental reports')
    for r in reports[:8]: render_card(r)

elif st.session_state.page=='Report an Issue':
    st.title('Report an environmental issue'); st.caption('Provide evidence and context. AI assists with categorization and structured analysis.')
    with st.form('report_form', clear_on_submit=True):
        title=st.text_input('Issue title', placeholder='e.g. Waste dumped beside a stream')
        category=st.selectbox('Category',['Water','Waste','Air','Climate','Biodiversity','Other'])
        location=st.text_input('Location', placeholder='e.g. Skardu, Gilgit-Baltistan')
        description=st.text_area('What did you observe?',height=150)
        image=st.file_uploader('Evidence photo (optional)',type=['jpg','jpeg','png','webp'])
        submitted=st.form_submit_button('Analyze & Submit',type='primary',use_container_width=True)
    if submitted:
        if not title.strip() or not location.strip() or not description.strip(): st.error('Please complete the title, location, and description.')
        else:
            with st.spinner('Analyzing the report...'):
                ai=analyze_environmental_report(title.strip(),category,location.strip(),description.strip(),image.getvalue() if image else None,image.type if image else None)
                rid=create_report(title.strip(),ai.get('category',category),location.strip(),description.strip(),image.getvalue() if image else None,ai)
            st.success('Report created successfully.'); st.session_state.selected_report=rid; st.session_state.page='Issue'; st.rerun()

elif st.session_state.page=='Issue':
    rid=st.session_state.get('selected_report'); r=get_report(rid) if rid else None
    if not r: st.warning('Select an issue from Home first.'); st.stop()
    st.title(r['title']); st.markdown(f'<span class="pill">{r["category"]}</span>&nbsp;{badge(r["status"])}',unsafe_allow_html=True); st.caption(f'📍 {r["location"]} · Report #{r["id"]} · {r["created_at"]}')
    a,b=st.columns([1.15,1])
    with a:
        if r['image_path'] and os.path.exists(r['image_path']): st.image(r['image_path'],use_container_width=True)
        else: st.info('No evidence image attached.')
        st.markdown('### Description'); st.write(r['description'])
    with b:
        st.markdown('### AI-assisted analysis'); ai=r['ai_analysis']; st.write(f"**Summary:** {ai.get('summary','')}"); st.write(f"**Priority:** {ai.get('priority','Medium')}"); st.write('**Possible causes:**'); [st.write(f'- {x}') for x in ai.get('possible_causes',[])]; st.write('**Suggested next actions:**'); [st.write(f'- {x}') for x in ai.get('next_actions',[])]; st.caption('AI output is advisory and should be independently verified.')
    st.divider(); st.markdown('### Issue status'); statuses=['Reported','Under Review','Verified','Action Required','Resolved']; choice=st.selectbox('Update status (demo/admin)',statuses,index=statuses.index(r['status']) if r['status'] in statuses else 0)
    if st.button('Save status',type='primary'): update_status(rid,choice); st.success('Status updated.'); st.rerun()
    st.divider(); st.markdown('### Community discussion'); comments=list_comments(rid)
    for c in comments: st.markdown(f"**{c['author']}** · {c['created_at']}"); st.write(c['comment']); st.divider()
    with st.form('comment_form',clear_on_submit=True):
        author=st.text_input('Your name',value='Demo User'); comment=st.text_area('Add a comment'); ok=st.form_submit_button('Post comment')
        if ok and comment.strip(): add_comment(rid,author.strip() or 'Anonymous',comment.strip()); st.success('Comment added.'); st.rerun()

elif st.session_state.page=='Innovation Lab':
    st.title('💡 Green Innovation Lab'); st.caption('Turn a real environmental problem into a practical solution and possible green-business opportunity.')
    reports=list_reports()
    if not reports: st.info('Create an environmental report first.'); st.stop()
    options={f'#{r["id"]} — {r["title"]} ({r["location"]})':r['id'] for r in reports}; label=st.selectbox('Choose a problem',list(options.keys())); r=get_report(options[label])
    st.markdown(f'<div class="card"><b>{r["title"]}</b><br><span class="small">{r["category"]} · {r["location"]}</span><br>{r["description"]}</div>',unsafe_allow_html=True)
    if st.button('Generate Green Solution',type='primary',use_container_width=True):
        with st.spinner('Generating innovation pathways...'): st.session_state.innovation_result=generate_green_innovation(r)
    if st.session_state.get('innovation_result'):
        idea=st.session_state.innovation_result; a,b=st.columns(2)
        with a: st.markdown('#### Problem'); st.write(idea.get('problem','')); st.markdown('#### Proposed solution'); st.write(idea.get('solution','')); st.markdown('#### How it could work'); st.write(idea.get('implementation',''))
        with b: st.markdown('#### Environmental benefit'); st.write(idea.get('environmental_benefit','')); st.markdown('#### Possible green-business model'); st.write(idea.get('business_model','')); st.markdown('#### First pilot'); st.write(idea.get('pilot',''))
        st.caption('AI-generated ideas are starting points and require local validation.')

else:
    st.title('📊 GRIP Dashboard'); reports=list_reports(); cats={}; stats={}
    for r in reports: cats[r['category']]=cats.get(r['category'],0)+1; stats[r['status']]=stats.get(r['status'],0)+1
    a,b=st.columns(2)
    with a: st.subheader('Issues by category'); st.bar_chart(cats) if cats else st.info('No reports yet.')
    with b: st.subheader('Issues by status'); st.bar_chart(stats) if stats else st.info('No data yet.')
    st.subheader('Recent reports')
    for r in reports[:15]: st.write(f"**#{r['id']} {r['title']}** — {r['category']} — {r['status']} — {r['location']}")
