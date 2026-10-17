"""
Streamlit UI for Local AI Model Manager
Provides web interface for model orchestration
"""

import streamlit as st
import asyncio
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional

from ollama_client import OllamaClient
from database import DatabaseManager
from resource_monitor import ResourceMonitor
from model_queue import ModelQueue, OperationStatus

# Configure page
st.set_page_config(
    page_title="Local AI Model Manager",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'queue' not in st.session_state:
    st.session_state.queue = ModelQueue()

if 'ollama_client' not in st.session_state:
    st.session_state.ollama_client = OllamaClient()

if 'db' not in st.session_state:
    st.session_state.db = DatabaseManager()

if 'resource_monitor' not in st.session_state:
    st.session_state.resource_monitor = ResourceMonitor()

# Start queue in a thread-safe way
if 'queue_started' not in st.session_state:
    try:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(st.session_state.queue.start())
        st.session_state.queue_started = True
    except Exception as e:
        st.error(f"Failed to start queue: {str(e)}")
        st.session_state.queue_started = False

def format_bytes(bytes_value: int) -> str:
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"

def format_timestamp(timestamp: str) -> str:
    """Format timestamp for display"""
    if not timestamp:
        return "Never"
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return timestamp

def refresh_data():
    """Refresh all data"""
    try:
        # Get models
        models = asyncio.run(st.session_state.ollama_client.list_models())
        running_models = asyncio.run(st.session_state.ollama_client.running_models())
        
        # Get system resources
        resources = st.session_state.resource_monitor.get_system_resources()
        
        # Get profiles
        profiles = st.session_state.db.get_profiles()
        
        # Get queue status
        queue_status = st.session_state.queue.get_queue_status()
        
        return models, running_models, resources, profiles, queue_status
    except Exception as e:
        st.error(f"Error refreshing data: {str(e)}")
        return [], [], None, [], {}

def main():
    st.title("🤖 Local AI Model Manager")
    
    # Sidebar
    with st.sidebar:
        st.header("Quick Actions")
        
        # Profile selector
        profiles = st.session_state.db.get_profiles()
        profile_names = [p['name'] for p in profiles]
        selected_profile = st.selectbox("Active Profile", profile_names, index=0)
        
        if st.button("Load Profile"):
            profile = next(p for p in profiles if p['name'] == selected_profile)
            st.info(f"Loading profile: {profile['name']}")
            # TODO: Implement profile loading
        
        # Resource alerts
        resources = st.session_state.resource_monitor.get_system_resources()
        alerts = st.session_state.resource_monitor.check_memory_thresholds()
        
        st.subheader("System Status")
        
        # RAM status
        ram_color = "🔴" if alerts['ram_high'] else "🟢"
        st.metric(f"{ram_color} RAM Usage", f"{resources.ram_percent:.1f}%")
        
        # GPU status
        if resources.gpu_info:
            gpu = resources.gpu_info[0]
            vram_color = "🔴" if alerts['vram_high'] else "🟢"
            st.metric(f"{vram_color} VRAM Usage", f"{gpu['memory_percent']:.1f}%")
        
        # CPU status
        st.metric("💻 CPU Usage", f"{resources.cpu_percent:.1f}%")
        
        if alerts['critical']:
            st.error("⚠️ Critical memory usage detected!")
    
    # Main content
    tab1, tab2, tab3, tab4 = st.tabs(["Models", "Operations", "Profiles", "Settings"])
    
    with tab1:
        st.header("Model Management")
        
        # Refresh button
        if st.button("🔄 Refresh", key="refresh_models"):
            st.rerun()
        
        # Get data
        models, running_models, resources, profiles, queue_status = asyncio.run(refresh_data())
        
        # Create two columns
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Installed Models")
            
            if models:
                model_data = []
                for model in models:
                    # Check if model is running
                    is_running = any(rm.model == model.name for rm in running_models)
                    
                    # Get model info from database
                    db_model = st.session_state.db.get_model(model.name)
                    usage_count = db_model['usage_count'] if db_model else 0
                    last_used = db_model['last_used'] if db_model else None
                    
                    model_data.append({
                        'Name': model.name,
                        'Size': format_bytes(model.size),
                        'Status': '🟢 Running' if is_running else '🔴 Stopped',
                        'Usage': usage_count,
                        'Last Used': format_timestamp(last_used) if last_used else 'Never'
                    })
                
                df = pd.DataFrame(model_data)
                st.dataframe(df, use_container_width=True)
                
                # Model actions
                st.subheader("Model Actions")
                selected_model = st.selectbox("Select Model", [m.name for m in models])
                
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                
                with col_btn1:
                    if st.button("▶️ Start", key="start_model"):
                        try:
                            asyncio.run(st.session_state.queue.load_model(selected_model))
                            st.success(f"Queued start for {selected_model}")
                        except Exception as e:
                            st.error(f"Failed to start {selected_model}: {str(e)}")

                with col_btn2:
                    if st.button("⏹️ Stop", key="stop_model"):
                        try:
                            asyncio.run(st.session_state.queue.unload_model(selected_model))
                            st.success(f"Queued stop for {selected_model}")
                        except Exception as e:
                            st.error(f"Failed to stop {selected_model}: {str(e)}")

                with col_btn3:
                    if st.button("🗑️ Delete", key="delete_model"):
                        if st.confirm(f"Delete {selected_model}? This cannot be undone!"):
                            try:
                                asyncio.run(st.session_state.queue.delete_model(selected_model))
                                st.success(f"Queued deletion for {selected_model}")
                            except Exception as e:
                                st.error(f"Failed to delete {selected_model}: {str(e)}")
            else:
                st.info("No models installed")
        
        with col2:
            st.subheader("Running Models")
            
            if running_models:
                for model in running_models:
                    with st.expander(f"🟢 {model.name}"):
                        st.write(f"**Size:** {format_bytes(model.size)}")
                        st.write(f"**Started:** {format_timestamp(model.created_at.isoformat())}")
                        
                        # Get detailed model info
                        model_info = asyncio.run(st.session_state.ollama_client.get_model_info(model.name))
                        if model_info:
                            st.write(f"**Architecture:** {model_info.architecture}")
                            st.write(f"**Parameters:** {model_info.parameters}")
                            st.write(f"**Context:** {model_info.context_length:,}")
                            st.write(f"**Capabilites:** {', '.join(model_info.capabilities)}")
                        
                        if st.button(f"⏹️ Stop {model.name}", key=f"stop_{model.name}"):
                            try:
                                asyncio.run(st.session_state.queue.unload_model(model.name))
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to stop {model.name}: {str(e)}")
            else:
                st.info("No models currently running")
            
            # Resource usage chart
            st.subheader("Resource Usage")
            
            # Create gauge charts
            col_gauge1, col_gauge2 = st.columns(2)
            
            with col_gauge1:
                fig_ram = go.Figure(go.Indicator(
                    mode = "gauge+number+delta",
                    value = resources.ram_percent,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "RAM Usage (%)"},
                    gauge = {
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, 50], 'color': "lightgray"},
                            {'range': [50, 80], 'color': "yellow"},
                            {'range': [80, 100], 'color': "red"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 85
                        }
                    }
                ))
                fig_ram.update_layout(height=300)
                st.plotly_chart(fig_ram, use_container_width=True)
            
            with col_gauge2:
                if resources.gpu_info:
                    gpu = resources.gpu_info[0]
                    fig_vram = go.Figure(go.Indicator(
                        mode = "gauge+number+delta",
                        value = gpu['memory_percent'],
                        domain = {'x': [0, 1], 'y': [0, 1]},
                        title = {'text': "VRAM Usage (%)"},
                        gauge = {
                            'axis': {'range': [None, 100]},
                            'bar': {'color': "darkgreen"},
                            'steps': [
                                {'range': [0, 50], 'color': "lightgray"},
                                {'range': [50, 85], 'color': "yellow"},
                                {'range': [85, 100], 'color': "red"}
                            ],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': 90
                            }
                        }
                    ))
                    fig_vram.update_layout(height=300)
                    st.plotly_chart(fig_vram, use_container_width=True)
                else:
                    st.info("No GPU detected")
    
    with tab2:
        st.header("Operations Queue")
        
        queue_status = st.session_state.queue.get_queue_status()
        
        # Queue status
        col_q1, col_q2, col_q3 = st.columns(3)
        with col_q1:
            st.metric("Queue Size", queue_status['queue_size'])
        with col_q2:
            st.metric("Active Operations", len(queue_status['active_operations']))
        with col_q3:
            st.metric("Total Completed", queue_status['total_completed'])
        
        # Active operations
        if queue_status['active_operations']:
            st.subheader("Active Operations")
            for op in queue_status['active_operations']:
                with st.expander(f"🔄 {op['type'].title()}: {op['model_name']} ({op['status'].title()})"):
                    st.write(f"**Started:** {format_timestamp(op['started_at'])}")
                    if op['error_message']:
                        st.error(f"Error: {op['error_message']}")
        else:
            st.info("No active operations")
        
        # Recent operations
        if queue_status['recent_operations']:
            st.subheader("Recent Operations")
            recent_df = pd.DataFrame(queue_status['recent_operations'])
            recent_df['duration'] = recent_df.apply(lambda row: 
                (datetime.fromisoformat(row['completed_at'].replace('Z', '+00:00')) - 
                 datetime.fromisoformat(row['started_at'].replace('Z', '+00:00'))).total_seconds()
                if row['started_at'] and row['completed_at'] else 0, axis=1)
            
            st.dataframe(recent_df[['type', 'model_name', 'status', 'duration']], use_container_width=True)
    
    with tab3:
        st.header("Model Profiles")
        
        profiles = st.session_state.db.get_profiles()
        
        for profile in profiles:
            with st.expander(f"📋 {profile['name']}"):
                st.write(f"**Models:** {', '.join(profile['models'])}")
                st.write(f"**Max Context:** {profile['max_context']:,}")
                st.write(f"**Auto Unload:** {profile['auto_unload_minutes']} minutes")
                st.write(f"**RAM Threshold:** {profile['ram_threshold']}%")
                
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    if st.button(f"🚀 Load {profile['name']}", key=f"load_{profile['name']}"):
                        st.info(f"Loading profile {profile['name']}...")
                        # TODO: Implement profile loading
                
                with col_p2:
                    if st.button(f"✏️ Edit {profile['name']}", key=f"edit_{profile['name']}"):
                        st.info("Profile editing coming soon")
    
    with tab4:
        st.header("Settings")
        
        st.subheader("Auto-Unload Settings")
        
        # Get current settings
        auto_unload_minutes = st.session_state.db.get_setting('auto_unload_minutes', '15')
        ram_threshold = st.session_state.db.get_setting('ram_threshold', '80')
        
        new_auto_unload = st.number_input("Auto-unload after (minutes)", 
                                         min_value=1, max_value=120, 
                                         value=int(auto_unload_minutes))
        
        new_ram_threshold = st.number_input("RAM threshold for auto-unload (%)", 
                                           min_value=50, max_value=95, 
                                           value=int(ram_threshold))
        
        if st.button("💾 Save Settings"):
            st.session_state.db.set_setting('auto_unload_minutes', str(new_auto_unload))
            st.session_state.db.set_setting('ram_threshold', str(new_ram_threshold))
            st.success("Settings saved!")
        
        st.subheader("System Information")
        
        # Ollama status
        try:
            models = asyncio.run(st.session_state.ollama_client.list_models())
            st.write(f"**Ollama Status:** 🟢 Connected")
            st.write(f"**Total Models:** {len(models)}")
        except:
            st.write("**Ollama Status:** 🔴 Not connected")
        
        # Database status
        st.write(f"**Database:** 🟢 Connected")
        
        # Queue status
        queue_status = st.session_state.queue.get_queue_status()
        st.write(f"**Queue:** 🟢 Running")

if __name__ == "__main__":
    main()
