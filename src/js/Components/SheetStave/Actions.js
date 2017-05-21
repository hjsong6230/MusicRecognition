import React from 'react';
import PropTypes from 'prop-types';

import SheetActions from 'omrActions/Sheet';
import ImageActions from 'omrActions/Image';

import Action from 'omrComponents/Common/ActionButton';

class Actions extends React.Component{
 componentDidMount(){
  const { store } = this.context;
  this.unsubscribe = store.subscribe(() =>
    this.forceUpdate()
  );
 }
 componentWillUnmount(){
  this.unsubscribe();
 }
 render(){
  const { store } = this.context;
  return(
   <div className="col-xs-3 content__actions content__actions--sheet">
    <Action className="action" text="Merge Section" onClick={() => {
      store.dispatch({ type: SheetActions.MERGE_STAVE_SECTIONS });
     }
    }/>
    <Action className="action" text="Edit Unstaved Image" onClick={() => {
      $('#unstaved').css('left', '0');
     }
    }/>
    <Action className="action" text="To Detect" onClick={() => {
      $('#crop').css('left', '0');
     }
    }/>
   </div>
  );
 }
}

Actions.contextTypes = {
 store: PropTypes.object
}

export default Actions;
